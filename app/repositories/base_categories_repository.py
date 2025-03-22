from typing import Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base_categories_model import BaseCategoriesModel
from app.repositories.base_repository import BaseRepository


class BaseCategoriesRepository(BaseRepository[BaseCategoriesModel]):
    def __init__(self, model: Type[BaseCategoriesModel]):
        super().__init__(model=model)

    async def get_category(
        self,
        session: AsyncSession,
        user_id: int,
        category_name: str,
    ) -> BaseCategoriesModel | None:
        query = select(self.model).filter(
            self.model.category_name.ilike(category_name),
            self.model.user_id == user_id,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
