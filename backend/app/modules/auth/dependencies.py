from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis

from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import DbSession
from app.integrations.redis import get_redis
from app.integrations.sms import SmsProvider
from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_sms_provider(request: Request) -> SmsProvider:
    return request.app.state.sms_provider


async def get_auth_service(
    session: DbSession,
    redis: Annotated[Redis, Depends(get_redis)],
    sms_provider: Annotated[SmsProvider, Depends(get_sms_provider)],
) -> AuthService:
    return AuthService(session, UserRepository(session), redis, sms_provider)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise AppError("Authentication required", status_code=401)
    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise AppError("Invalid or expired access token", status_code=401) from exc
    return await UserService(UserRepository(session)).get_active_user(user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]
