from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar('T')


class BaseCategoriesService(Generic[T]):
    def __init__(self, category_repo, default_category_name: str):
        self.category_repo = category_repo
        self.default_category_name = default_category_name

    async def is_category_exists(
        self,
        category_name: str,
        session: AsyncSession,
    ) -> bool:
        category = await self.category_repo.get_by_filter(
            session,
            dict(
                name=category_name,
            ),
        )
        return bool(category)

    async def add_category_to_db(
        self,
        category_name: str,
        session: AsyncSession,
    ):
        category = await self.category_repo.add(
            session,
            dict(
                name=category_name
            ),
        )
        return category

    async def get_default_category(
        self,
        session: AsyncSession,
    ):
        category = await self.category_repo.get_by_filter(
            session,
            dict(
                name=self.default_category_name,
            ),
        )
        if category:
            return category
        else:
            return await self.add_category_to_db(
                self.default_category_name,
                session,
            )

    async def get_category_by_name(
        self,
        name: str,
        session: AsyncSession,
    ):
        category = await self.category_repo.get_by_filter(
            session,
            dict(
                name=name,
            ),
        )
        return category
