from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from redis.asyncio import Redis

from app.core.exceptions import AppError
from app.integrations.sms import SmsProvider
from app.modules.auth.schemas import OtpRequest, OtpVerify
from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


@pytest.mark.parametrize(
    ("provided", "normalized"),
    [
        ("09121234567", "+989121234567"),
        ("989121234567", "+989121234567"),
        ("0098 912 123 4567", "+989121234567"),
        ("۰۹۱۲۱۲۳۴۵۶۷", "+989121234567"),
        ("٠٩١٢١٢٣٤٥٦٧", "+989121234567"),
    ],
)
def test_iranian_phone_numbers_are_normalized(provided: str, normalized: str) -> None:
    assert OtpRequest(phone_number=provided).phone_number == normalized


@pytest.mark.parametrize("phone_number", ["02112345678", "+14155552671", "091234"])
def test_non_mobile_phone_numbers_are_rejected(phone_number: str) -> None:
    with pytest.raises(ValidationError, match="valid Iranian mobile"):
        OtpRequest(phone_number=phone_number)


async def test_request_otp_stores_hash_and_sends_code() -> None:
    redis = AsyncMock(spec=Redis)
    redis.set = AsyncMock(return_value=True)
    sms = AsyncMock(spec=SmsProvider)
    service = AuthService(AsyncMock(), AsyncMock(spec=UserRepository), redis, sms)

    result = await service.request_otp(OtpRequest(phone_number="09121234567"))

    assert result.expires_in == 300
    sms.send_otp.assert_awaited_once()
    phone_number, code = sms.send_otp.await_args.args
    assert phone_number == "+989121234567"
    assert len(code) == 6 and code.isdigit()
    redis.execute_command.assert_any_await(
        "HSET",
        service._phone_key(phone_number, "otp"),
        "code",
        service._otp_digest(phone_number, code),
        "attempts",
        "0",
    )


async def test_request_otp_enforces_phone_cooldown() -> None:
    redis = AsyncMock(spec=Redis)
    redis.set = AsyncMock(return_value=None)
    service = AuthService(
        AsyncMock(), AsyncMock(spec=UserRepository), redis, AsyncMock(spec=SmsProvider)
    )

    with pytest.raises(AppError, match="wait before requesting") as error:
        await service.request_otp(OtpRequest(phone_number="09121234567"))

    assert error.value.status_code == 429


async def test_verify_otp_creates_phone_user_and_returns_token() -> None:
    now = datetime.now(UTC)
    user = User(
        id=uuid4(),
        phone_number="+989121234567",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    redis = AsyncMock(spec=Redis)
    redis.execute_command.return_value = 1
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_phone_number.return_value = None
    repository.create_with_phone_number.return_value = user
    session = AsyncMock()

    result = await AuthService(session, repository, redis).verify_otp(
        OtpVerify(phone_number="09121234567", code="123456")
    )

    assert result.user.phone_number == "+989121234567"
    assert result.access_token
    repository.create_with_phone_number.assert_awaited_once_with("+989121234567")
    session.commit.assert_awaited_once()


@pytest.mark.parametrize(("redis_result", "status_code"), [(-1, 401), (0, 401), (-2, 429)])
async def test_verify_otp_rejects_invalid_expired_and_exhausted_codes(
    redis_result: int, status_code: int
) -> None:
    redis = AsyncMock(spec=Redis)
    redis.execute_command.return_value = redis_result
    service = AuthService(AsyncMock(), AsyncMock(spec=UserRepository), redis)

    with pytest.raises(AppError) as error:
        await service.verify_otp(OtpVerify(phone_number="09121234567", code="123456"))

    assert error.value.status_code == status_code
