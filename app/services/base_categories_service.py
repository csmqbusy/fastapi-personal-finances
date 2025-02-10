from typing import Generic, TypeVar, Type

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar('T')


class BaseCategoriesService(Generic[T]):
    def __init__(
        self,
        category_repo,
        user_categories_repo,
        default_category_name: str,
        out_schema: Type[BaseModel],
    ):
        self.category_repo = category_repo
        self.user_category_repo = user_categories_repo
        self.default_category_name = default_category_name
        self.out_schema = out_schema

    async def is_category_exists(
        self,
        category_name: str,
        session: AsyncSession,
    ) -> bool:
        category = await self.category_repo.get_by_filter(
            session,
            dict(name=category_name),
        )
        return bool(category)

    async def add_category_to_db(
        self,
        category_name: str,
        user_id: int,
        session: AsyncSession,
    ):
        category = await self.category_repo.add(
            session,
            dict(name=category_name),
        )
        await self.user_category_repo.add(
            session,
            dict(user_id=user_id, category_id=category.id),
        )
        return self.out_schema.model_validate(category)

    async def get_default_category(
        self,
        user_id: int,
        session: AsyncSession,
    ):
        category = await self.category_repo.get_by_filter(
            session,
            dict(name=self.default_category_name),
        )
        if category:
            return self.out_schema.model_validate(category)
        else:
            return await self.add_category_to_db(
                self.default_category_name,
                user_id,
                session,
            )

    async def get_category_by_name(
        self,
        name: str,
        session: AsyncSession,
    ):
        category = await self.category_repo.get_by_filter(
            session,
            dict(name=name),
        )
        return self.out_schema.model_validate(category)
