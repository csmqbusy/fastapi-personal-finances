from typing import Type

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.categories_exceptions import CategoryNotFound


class TransactionsService:
    def __init__(
        self,
        tx_repo,
        tx_categories_repo,
        default_tx_category_name: str,
        creation_schema: Type[BaseModel],
        creation_in_db_schema: Type[BaseModel],
        out_schema: Type[BaseModel],
    ):
        self.tx_repo = tx_repo
        self.tx_categories_repo = tx_categories_repo
        self.default_tx_category_name = default_tx_category_name
        self.creation_schema = creation_schema
        self.creation_in_db_schema = creation_in_db_schema
        self.out_schema = out_schema

    async def _get_category_id(
        self,
        user_id: int,
        category_name: str,
        session: AsyncSession,
    ) -> int:
        category = await self.tx_categories_repo.get_one_by_filter(
            session,
            dict(user_id=user_id, category_name=category_name),
        )
        if not category:
            raise CategoryNotFound
        return category.id
