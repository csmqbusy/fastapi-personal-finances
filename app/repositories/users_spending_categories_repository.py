from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UsersSpendingCategoriesModel
from app.repositories.base_repository import BaseRepository


class UserSpendingCategoriesRepository(
    BaseRepository[UsersSpendingCategoriesModel]
):
    def __init__(self):
        super().__init__(UsersSpendingCategoriesModel)

    async def get_category(
        self,
        session: AsyncSession,
        user_id: int,
        category_name: str,
    ) -> UsersSpendingCategoriesModel | None:
        query = (
            select(self.model)
            .filter(
                self.model.category_name.ilike(category_name),
                self.model.user_id == user_id,
            )
        )
        user = await session.execute(query)
        return user.scalar_one_or_none()


user_spend_cat_repo = UserSpendingCategoriesRepository()
