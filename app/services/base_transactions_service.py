from typing import Type, Any

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

    async def add_transaction_to_db(
        self,
        transaction: Type[BaseModel],
        user_id: int,
        session: AsyncSession,
    ):
        category_name = transaction.category_name
        if not category_name:
            category_name = self.default_tx_category_name
        category_id = await self._get_category_id(
            user_id, category_name, session)
        transaction_to_create = self.creation_in_db_schema(
            amount=transaction.amount,
            description=transaction.description,
            user_id=user_id,
            category_id=category_id,
        )
        transaction_from_db = await self.tx_repo.add(
            session,
            transaction_to_create.model_dump(),
        )
        transaction_out = self.out_schema.model_validate(transaction_from_db)
        transaction_out.category_name = category_name
        return transaction_out

    async def get_all_transactions_by_category(
        self,
        category_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> list[Any]:
        transactions = await self.tx_repo.get_all_by_filter(
            session,
            dict(category_id=category_id, user_id=user_id),
        )
        return transactions

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
