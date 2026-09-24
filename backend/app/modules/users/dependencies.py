from typing import Annotated

from fastapi import Depends

from app.db.session import DbSession
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


async def get_user_service(session: DbSession) -> UserService:
    return UserService(UserRepository(session))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
