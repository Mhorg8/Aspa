from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import UUID

import jwt
import pytest
from httpx import AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import verify_password
from app.integrations.redis import get_redis
from app.integrations.sms import LocalSmsProvider
from app.main import app
from app.modules.users.models import User
from app.modules.users.repository import UserRepository

pytestmark = pytest.mark.integration
CREDENTIALS = {"email": "athlete@example.com", "password": "strong-password"}


async def test_phone_otp_signup(integration_client: AsyncClient, db_session: AsyncSession) -> None:
    requested = await integration_client.post(
        "/api/auth/otp/request", json={"phone_number": "۰۹۱۲۱۲۳۴۵۶۷"}
    )
    assert requested.status_code == 202, requested.text
    provider = app.state.sms_provider
    assert isinstance(provider, LocalSmsProvider)
    code = provider.sent_codes["+989121234567"]

    verified = await integration_client.post(
        "/api/auth/otp/verify",
        json={"phone_number": "09121234567", "code": code},
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["user"]["phone_number"] == "+989121234567"
    user = await db_session.scalar(select(User).where(User.phone_number == "+989121234567"))
    assert user is not None
    assert user.email is None
    assert user.hashed_password is None


async def test_full_auth_flow(integration_client: AsyncClient, db_session: AsyncSession) -> None:
    client = integration_client
    registered = await client.post("/api/auth/register", json=CREDENTIALS)
    assert registered.status_code == 201, registered.text
    assert "hashed_password" not in registered.text
    user = await db_session.get(User, UUID(registered.json()["user"]["id"]))
    assert user is not None
    assert user.hashed_password != CREDENTIALS["password"]
    assert verify_password(CREDENTIALS["password"], user.hashed_password)

    duplicate = await client.post(
        "/api/auth/register", json={**CREDENTIALS, "email": "ATHLETE@example.com"}
    )
    assert duplicate.status_code == 409
    login = await client.post("/api/auth/login", json=CREDENTIALS)
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = await client.get("/api/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["id"] == str(user.id)

    user.is_active = False
    await db_session.commit()
    assert (await client.get("/api/users/me", headers=headers)).status_code == 401
    assert (await client.post("/api/auth/login", json=CREDENTIALS)).status_code == 403


@pytest.mark.parametrize("authorization", [None, "Bearer garbage", "Basic garbage"])
async def test_protected_route_rejects_invalid_auth(
    integration_client: AsyncClient, authorization: str | None
) -> None:
    headers = {"Authorization": authorization} if authorization else {}
    response = await integration_client.get("/api/users/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_wrong_and_unknown_credentials(integration_client: AsyncClient) -> None:
    await integration_client.post("/api/auth/register", json=CREDENTIALS)
    for credentials in [
        {**CREDENTIALS, "password": "incorrect-password"},
        {**CREDENTIALS, "email": "missing@example.com"},
    ]:
        response = await integration_client.post("/api/auth/login", json=credentials)
        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Invalid email or password"
        assert response.headers["www-authenticate"] == "Bearer"


async def test_real_redis_rate_limit(integration_client: AsyncClient) -> None:
    # Invalid input consumes the same request budget without doing expensive hashing.
    for _ in range(get_settings().auth_rate_limit_requests):
        response = await integration_client.post("/api/auth/login", json={})
        assert response.status_code == 422
    response = await integration_client.post("/api/auth/register", json=CREDENTIALS)
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0


async def test_registration_validation(
    integration_client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await integration_client.post(
        "/api/auth/register", json={**CREDENTIALS, "password": "short"}
    )
    assert response.status_code == 422
    assert (await db_session.execute(select(User))).scalars().all() == []


async def test_database_duplicate_race_is_handled(
    integration_client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = await integration_client.post("/api/auth/register", json=CREDENTIALS)
    assert registered.status_code == 201
    # Simulate a stale pre-insert read; PostgreSQL must enforce the unique index.
    monkeypatch.setattr(UserRepository, "get_by_email", AsyncMock(return_value=None))
    duplicate = await integration_client.post("/api/auth/register", json=CREDENTIALS)
    assert duplicate.status_code == 409, duplicate.text
    assert len((await db_session.execute(select(User))).scalars().all()) == 1


async def test_expired_bearer_rejected(integration_client: AsyncClient) -> None:
    registered = await integration_client.post("/api/auth/register", json=CREDENTIALS)
    past = datetime.now(UTC) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": registered.json()["user"]["id"], "iat": past, "exp": past},
        get_settings().jwt_secret_key,
        algorithm="HS256",
    )
    response = await integration_client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_redis_outage_fails_closed(integration_client: AsyncClient) -> None:
    unavailable = AsyncMock()
    unavailable.execute_command.side_effect = RedisConnectionError("test outage")
    unavailable.ping.side_effect = RedisConnectionError("test outage")

    async def override_redis() -> AsyncMock:
        return unavailable

    app.dependency_overrides[get_redis] = override_redis
    response = await integration_client.post("/api/auth/login", json=CREDENTIALS)
    assert response.status_code == 503
    ready = await integration_client.get("/ready")
    assert ready.status_code == 503
    assert ready.json()["error"]["code"] == "service_unavailable"


async def test_health_and_readiness(integration_client: AsyncClient) -> None:
    health = await integration_client.get("/health")
    ready = await integration_client.get("/ready")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert ready.status_code == 200, ready.text
    assert ready.json() == {
        "status": "ready",
        "checks": {"database": "ok", "redis": "ok"},
    }


async def test_validation_and_not_found_use_error_envelope(
    integration_client: AsyncClient,
) -> None:
    validation = await integration_client.post("/api/auth/login", json={})
    missing = await integration_client.get("/does-not-exist")
    assert validation.status_code == 422
    assert validation.json()["error"]["code"] == "validation_error"
    assert validation.json()["error"]["details"]
    assert missing.status_code == 404
    assert missing.json() == {"error": {"code": "http_error", "message": "Not Found"}}


async def test_openapi_uses_unversioned_api_contract(integration_client: AsyncClient) -> None:
    schema = (await integration_client.get("/openapi.json")).json()
    assert "/api/auth/login" in schema["paths"]
    assert "/api/users/me" in schema["paths"]
    assert all("/api/v1" not in path for path in schema["paths"])
    assert "ErrorResponse" in schema["components"]["schemas"]
