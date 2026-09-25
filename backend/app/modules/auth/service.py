import hashlib
import hmac
import secrets
from typing import cast

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.integrations.sms import SmsProvider
from app.modules.auth.schemas import (
    AuthResponse,
    Credentials,
    OtpRequest,
    OtpRequestResponse,
    OtpVerify,
)
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse

_VERIFY_OTP = """
local expected = redis.call('HGET', KEYS[1], 'code')
if not expected then return -1 end
local attempts = tonumber(redis.call('HGET', KEYS[1], 'attempts') or '0')
if attempts >= tonumber(ARGV[2]) then return -2 end
if expected ~= ARGV[1] then
    attempts = redis.call('HINCRBY', KEYS[1], 'attempts', 1)
    if attempts >= tonumber(ARGV[2]) then return -2 end
    return 0
end
redis.call('DEL', KEYS[1])
redis.call('DEL', KEYS[2])
return 1
"""


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        users: UserRepository,
        redis: Redis | None = None,
        sms_provider: SmsProvider | None = None,
    ) -> None:
        self.session = session
        self.users = users
        self.redis = redis
        self.sms_provider = sms_provider

    @staticmethod
    def _phone_key(phone_number: str, purpose: str) -> str:
        settings = get_settings()
        identifier = hmac.new(
            settings.jwt_secret_key.encode(), phone_number.encode(), hashlib.sha256
        ).hexdigest()
        return f"aspa:{settings.environment}:auth:{purpose}:{identifier}"

    @staticmethod
    def _otp_digest(phone_number: str, code: str) -> str:
        secret = get_settings().jwt_secret_key.encode()
        return hmac.new(secret, f"{phone_number}:{code}".encode(), hashlib.sha256).hexdigest()

    async def request_otp(self, data: OtpRequest) -> OtpRequestResponse:
        if self.redis is None or self.sms_provider is None:
            raise RuntimeError("OTP dependencies are not configured")
        settings = get_settings()
        otp_key = self._phone_key(data.phone_number, "otp")
        cooldown_key = self._phone_key(data.phone_number, "otp-cooldown")
        try:
            allowed = await self.redis.set(
                cooldown_key,
                "1",
                ex=settings.otp_resend_cooldown_seconds,
                nx=True,
            )
            if not allowed:
                raise AppError(
                    "Please wait before requesting another OTP",
                    status_code=429,
                    headers={"Retry-After": str(settings.otp_resend_cooldown_seconds)},
                )
            code = f"{secrets.randbelow(1_000_000):06d}"
            await self.redis.execute_command(  # pyright: ignore[reportUnknownMemberType]
                "HSET",
                otp_key,
                "code",
                self._otp_digest(data.phone_number, code),
                "attempts",
                "0",
            )
            await self.redis.execute_command(  # pyright: ignore[reportUnknownMemberType]
                "EXPIRE", otp_key, settings.otp_expire_seconds
            )
            try:
                await self.sms_provider.send_otp(data.phone_number, code)
            except Exception as exc:
                await self.redis.delete(otp_key, cooldown_key)
                raise AppError("Could not send OTP", status_code=503) from exc
        except RedisError as exc:
            raise AppError("Authentication temporarily unavailable", status_code=503) from exc
        return OtpRequestResponse(expires_in=settings.otp_expire_seconds)

    async def verify_otp(self, data: OtpVerify) -> AuthResponse:
        if self.redis is None:
            raise RuntimeError("OTP dependencies are not configured")
        settings = get_settings()
        otp_key = self._phone_key(data.phone_number, "otp")
        cooldown_key = self._phone_key(data.phone_number, "otp-cooldown")
        try:
            result = cast(
                int,
                await self.redis.execute_command(  # pyright: ignore[reportUnknownMemberType]
                    "EVAL",
                    _VERIFY_OTP,
                    2,
                    otp_key,
                    cooldown_key,
                    self._otp_digest(data.phone_number, data.code),
                    settings.otp_max_attempts,
                ),
            )
        except RedisError as exc:
            raise AppError("Authentication temporarily unavailable", status_code=503) from exc
        if result == -1:
            raise AppError("OTP is invalid or expired", status_code=401)
        if result == -2:
            raise AppError("Too many invalid OTP attempts", status_code=429)
        if result == 0:
            raise AppError("OTP is invalid or expired", status_code=401)

        user = await self.users.get_by_phone_number(data.phone_number)
        if user is None:
            try:
                user = await self.users.create_with_phone_number(data.phone_number)
                await self.session.commit()
            except IntegrityError:
                await self.session.rollback()
                user = await self.users.get_by_phone_number(data.phone_number)
                if user is None:
                    raise
        if not user.is_active:
            raise AppError("User is inactive", status_code=403)
        return AuthResponse(
            access_token=create_access_token(user.id),
            user=UserResponse.model_validate(user),
        )

    async def register(self, data: Credentials) -> AuthResponse:
        email = data.email.lower()
        if await self.users.get_by_email(email) is not None:
            raise AppError("A user with this email already exists", status_code=409)

        try:
            hashed_password = await run_in_threadpool(hash_password, data.password)
            user = await self.users.create(email=email, hashed_password=hashed_password)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            cause = exc.orig.__cause__ if exc.orig is not None else None
            if (
                getattr(cause, "sqlstate", None) != "23505"
                or getattr(cause, "constraint_name", None) != "ix_users_email"
            ):
                raise
            raise AppError("A user with this email already exists", status_code=409) from exc

        return AuthResponse(
            access_token=create_access_token(user.id),
            user=UserResponse.model_validate(user),
        )

    async def login(self, data: Credentials) -> AuthResponse:
        user = await self.users.get_by_email(data.email.lower())
        if user is None:
            # Match the expensive password work on the unknown-user path.
            await run_in_threadpool(hash_password, data.password)
            raise AppError("Invalid email or password", status_code=401)
        if user.hashed_password is None or not await run_in_threadpool(
            verify_password, data.password, user.hashed_password
        ):
            raise AppError("Invalid email or password", status_code=401)
        if not user.is_active:
            raise AppError("User is inactive", status_code=403)
        return AuthResponse(
            access_token=create_access_token(user.id),
            user=UserResponse.model_validate(user),
        )
