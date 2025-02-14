from typing import Generic, TypeVar, Type

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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
