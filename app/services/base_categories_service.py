from typing import Generic, TypeVar, Type

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.categories_exceptions import CategoryAlreadyExists

T = TypeVar('T')


class BaseCategoriesService(Generic[T]):
    def __init__(
        self,
        category_repo,
        default_category_name: str,
        out_schema: Type[BaseModel],
    ):
        self.category_repo = category_repo
        self.default_category_name = default_category_name
        self.out_schema = out_schema

    async def get_category(
        self,
        user_id: int,
        category_name: str,
        session: AsyncSession,
    ) -> T | None:
        category = await self.category_repo.get_one_by_filter(
            session,
            dict(user_id=user_id, category_name=category_name),
        )
        return category

    async def add_category_to_db(
        self,
        user_id: int,
        category_name: str,
        session: AsyncSession,
    ):
        category = await self.get_category(user_id, category_name, session)
        if category:
            raise CategoryAlreadyExists
        category = await self.category_repo.add(
            session,
            dict(user_id=user_id, category_name=category_name),
        )
        return self.out_schema.model_validate(category)

    async def get_user_categories(
        self,
        user_id: int,
        session: AsyncSession,
    ):
        user_categories = await self.category_repo.get_all_by_filter(
            session,
            dict(user_id=user_id),
        )
        return user_categories

    async def is_category_exists(
        self,
        user_id: int,
        category_name: str,
        session: AsyncSession,
    ):
        user_categories = await self.get_user_categories(
            user_id,
            session,
        )
        categories = [c.category_name for c in user_categories]
        return category_name in categories
