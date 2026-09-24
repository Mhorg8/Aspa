from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, decode_access_token


def test_missing_secret_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="production")


@pytest.mark.parametrize("secret", ["short", "development-only-secret-change-me"])
def test_unsafe_secret_rejected(secret: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret_key=secret)


def test_access_token_round_trip() -> None:
    uid = uuid4()
    assert decode_access_token(create_access_token(uid)) == uid


@pytest.mark.parametrize("missing", ["exp", "iat", "sub"])
def test_required_claims(missing: str) -> None:
    now = datetime.now(UTC)
    payload = {"sub": str(uuid4()), "iat": now, "exp": now + timedelta(minutes=1)}
    del payload[missing]
    token = jwt.encode(payload, get_settings().jwt_secret_key, algorithm="HS256")
    with pytest.raises(ValueError, match="Invalid access token"):
        decode_access_token(token)


def test_expired_token_rejected() -> None:
    past = datetime.now(UTC) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": str(uuid4()), "iat": past, "exp": past},
        get_settings().jwt_secret_key,
        algorithm="HS256",
    )
    with pytest.raises(ValueError):
        decode_access_token(token)
