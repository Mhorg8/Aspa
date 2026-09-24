from uuid import UUID

from app.core.exceptions import AppError
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def get_active_user(self, user_id: UUID) -> User:
        user = await self.repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AppError("User not found or inactive", status_code=401)
        return user
