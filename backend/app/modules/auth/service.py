from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.schemas import AuthResponse, Credentials
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse


class AuthService:
    def __init__(self, session: AsyncSession, users: UserRepository) -> None:
        self.session = session
        self.users = users

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
        if not await run_in_threadpool(verify_password, data.password, user.hashed_password):
            raise AppError("Invalid email or password", status_code=401)
        if not user.is_active:
            raise AppError("User is inactive", status_code=403)
        return AuthResponse(
            access_token=create_access_token(user.id),
            user=UserResponse.model_validate(user),
        )
