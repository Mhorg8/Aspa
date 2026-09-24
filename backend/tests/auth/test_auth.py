from datetime import UTC, datetime
from threading import get_ident
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.main import app
from app.modules.auth import service as service_module
from app.modules.auth.dependencies import get_auth_service, get_current_user
from app.modules.auth.schemas import AuthResponse, Credentials
from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse


def make_user(password: str = "strong-password") -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="athlete@example.com",
        hashed_password=hash_password(password),
        is_active=True,
        created_at=now,
        updated_at=now,
    )


async def test_login_returns_token_for_valid_credentials() -> None:
    user = make_user()
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = user
    session = AsyncMock()
    service = AuthService(session, repository)

    result = await service.login(
        Credentials(email="athlete@example.com", password="strong-password")
    )

    assert result.token_type == "bearer"
    assert result.access_token
    assert result.user.email == user.email


async def test_login_rejects_wrong_password() -> None:
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = make_user()
    service = AuthService(AsyncMock(), repository)

    with pytest.raises(AppError, match="Invalid email or password"):
        await service.login(Credentials(email="athlete@example.com", password="wrong-password"))


async def test_auth_routes_and_current_user(client: AsyncClient) -> None:
    user = make_user()
    response = AuthResponse(
        access_token="test-token",
        user=UserResponse.model_validate(user),
    )
    auth_service = AsyncMock(spec=AuthService)
    auth_service.register.return_value = response
    auth_service.login.return_value = response

    async def override_auth_service() -> AuthService:
        return auth_service

    async def override_current_user() -> User:
        return user

    app.dependency_overrides[get_auth_service] = override_auth_service
    app.dependency_overrides[get_current_user] = override_current_user

    register = await client.post(
        "/api/auth/register",
        json={"email": user.email, "password": "strong-password"},
    )
    login = await client.post(
        "/api/auth/login",
        json={"email": user.email, "password": "strong-password"},
    )
    me = await client.get("/api/users/me")

    assert register.status_code == 201
    assert login.status_code == 200
    assert me.status_code == 200
    assert me.json()["email"] == user.email


async def test_password_verification_runs_off_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    event_loop_thread = get_ident()
    user = make_user()
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = user

    def verify_in_worker(password: str, hashed: str) -> bool:
        assert get_ident() != event_loop_thread
        return True

    monkeypatch.setattr(service_module, "verify_password", verify_in_worker)
    await AuthService(AsyncMock(), repository).login(
        Credentials(email=user.email, password="strong-password")
    )


async def test_unrelated_integrity_error_is_not_reported_as_duplicate() -> None:
    session = AsyncMock()
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = None
    repository.create.side_effect = IntegrityError("insert", {}, Exception("not-null violation"))
    with pytest.raises(IntegrityError):
        await AuthService(session, repository).register(
            Credentials(email="athlete@example.com", password="strong-password")
        )
    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
