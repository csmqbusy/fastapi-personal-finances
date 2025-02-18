from typing import Type, Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.categories_exceptions import (
    CategoryNotFound,
    MissingCategory,
)
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.schemas.date_range_schemas import SDateRange
from app.schemas.spendings_schemas import (
    STransactionsQueryParams,
    STransactionsSortParams,
    SortParam,
)


class TransactionsService:
    def __init__(
        self,
        tx_repo,
        tx_categories_repo,
        default_tx_category_name: str,
        creation_schema: Type[BaseModel],
        creation_in_db_schema: Type[BaseModel],
        update_partial_in_db_schema: Type[BaseModel],
        out_schema: Type[BaseModel],
    ):
        self.tx_repo = tx_repo
        self.tx_categories_repo = tx_categories_repo
        self.default_tx_category_name = default_tx_category_name
        self.creation_schema = creation_schema
        self.creation_in_db_schema = creation_in_db_schema
        self.update_partial_in_db_schema = update_partial_in_db_schema
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
            user_id, category_name, session
        )
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

    async def update_transaction(
        self,
        transaction_id: int,
        user_id: int,
        transaction_update_obj: Type[BaseModel],
        session: AsyncSession,
    ):
        transaction = await self.tx_repo.get_transaction_with_category(
            session,
            transaction_id,
        )
        if not transaction or transaction.user_id != user_id:
            raise TransactionNotFound

        transaction_to_update = self.update_partial_in_db_schema(
            amount=transaction_update_obj.amount,
            description=transaction_update_obj.description,
        )

        new_cat_name = transaction_update_obj.category_name
        if new_cat_name and new_cat_name != transaction.category.category_name:
            new_category = await self.tx_categories_repo.get_one_by_filter(
                session,
                dict(user_id=user_id, category_name=new_cat_name),
            )
            if new_category is None:
                raise CategoryNotFound
            transaction.category_id = new_category.id
            await session.commit()
            await session.refresh(transaction)

        updated_transaction = await self.tx_repo.update(
            session,
            transaction_id,
            transaction_to_update.model_dump(exclude_none=True),
        )

        transaction_out = self.out_schema(
            amount=updated_transaction.amount,
            description=updated_transaction.description,
            category_name=transaction.category.category_name,
            date=updated_transaction.date,
            id=updated_transaction.id,
        )
        return transaction_out

    async def get_transaction(
        self,
        transaction_id: int,
        user_id: int,
        session: AsyncSession,
    ):
        transaction = await self.tx_repo.get_transaction_with_category(
            session, transaction_id
        )
        if not transaction or transaction.user_id != user_id:
            raise TransactionNotFound

        transaction_out = self.out_schema(
            amount=transaction.amount,
            description=transaction.description,
            category_name=transaction.category.category_name,
            date=transaction.date,
            id=transaction.id,
        )
        return transaction_out

    async def get_all_transactions_by_category(
        self,
        session: AsyncSession,
        user_id: int,
        category_id: int | None = None,
        category_name: str | None = None,
    ) -> list[Any]:
        if category_id is None and category_name is None:
            raise MissingCategory

        if category_id is None:
            category_id = await self._get_category_id(
                user_id, category_name, session
            )

        transactions = await self.tx_repo.get_all(
            params=dict(category_id=category_id, user_id=user_id),
            order_by="id",
            order_direction="desc",
            session=session,
        )
        return transactions

    async def get_all_user_transactions(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> list[Any]:
        transactions = await self.tx_repo.get_all(
            params=dict(user_id=user_id),
            order_by="id",
            order_direction="desc",
            session=session,
        )
        return transactions

    async def delete_transaction(
        self,
        transaction_id: int,
        user_id: int,
        session: AsyncSession,
    ):
        transaction = await self.tx_repo.get(session, transaction_id)
        if not transaction or transaction.user_id != user_id:
            raise TransactionNotFound
        await self.tx_repo.delete(session, transaction_id)

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

    async def get_transactions(
        self,
        session: AsyncSession,
        query_params: STransactionsQueryParams,
        date_range: SDateRange,
        sort_params: STransactionsSortParams | None,
    ):
        if query_params.category_name and query_params.category_id is None:
            category = await self.tx_categories_repo.get_one_by_filter(
                session,
                dict(
                    user_id=query_params.user_id,
                    category_name=query_params.category_name,
                ),
            )
            if not category:
                raise CategoryNotFound
            query_params.category_id = category.id

        query_params.category_name = None
        if sort_params:
            sort_params = self._parse_sort_params_for_query(sort_params)

        return await self.tx_repo.get_transactions(
            session,
            query_params.model_dump(exclude_none=True),
            sort_params=sort_params,
            date_from=date_range.start,
            date_to=date_range.end,
        )

    @staticmethod
    def _parse_sort_params_for_query(
        sort_params: STransactionsSortParams,
    ) -> list[SortParam]:
        result = []

        for param in sort_params.sort_by:
            if param.startswith("-"):
                result.append(
                    SortParam(
                        order_by=param.lstrip("-"),
                        order_direction="desc",
                    ),
                )
            else:
                result.append(
                    SortParam(
                        order_by=param,
                        order_direction="asc",
                    ),
                )

        return result
