from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    def __init__(self):
        super().__init__(UserModel)

    async def get_by_username(
        self,
        session: AsyncSession,
        username: str,
    ) -> UserModel | None:
        query = select(self.model).filter(self.model.username.ilike(username))
        user = await session.execute(query)
        return user.scalar_one_or_none()

    async def get_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> UserModel | None:
        query = select(self.model).filter(self.model.email.ilike(email))
        user = await session.execute(query)
        return user.scalar_one_or_none()


user_repo = UserRepository()
