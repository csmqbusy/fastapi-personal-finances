from collections import defaultdict
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.categories_exceptions import (
    CategoryNotFound,
)
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.repositories import (
    BaseCategoriesRepository,
    BaseTransactionsRepository,
)
from app.schemas.transaction_category_schemas import SCategoryQueryParams
from app.schemas.transactions_schemas import (
    STransactionsSortParams,
    STransactionCreate,
    STransactionResponse,
    STransactionUpdatePartialInDB,
    STransactionCreateInDB,
    STransactionUpdatePartial,
    STransactionsSummary,
)
from app.schemas.common_schemas import (
    SAmountRange,
    SDatetimeRange,
)
from app.services.common_service import parse_sort_params_for_query


class TransactionsService:
    def __init__(
        self,
        tx_repo: BaseTransactionsRepository,
        tx_categories_repo: BaseCategoriesRepository,
        default_tx_category_name: str,
        creation_schema: Type[STransactionCreate],
        creation_in_db_schema: Type[STransactionCreateInDB],
        update_partial_in_db_schema: Type[STransactionUpdatePartialInDB],
        out_schema: Type[STransactionResponse],
    ) -> None:
        self.tx_repo = tx_repo
        self.tx_categories_repo = tx_categories_repo
        self.default_tx_category_name = default_tx_category_name
        self.creation_schema = creation_schema
        self.creation_in_db_schema = creation_in_db_schema
        self.update_partial_in_db_schema = update_partial_in_db_schema
        self.out_schema = out_schema

    async def add_transaction_to_db(
        self,
        transaction: STransactionCreate,
        user_id: int,
        session: AsyncSession,
    ) -> STransactionResponse:
        category_name = transaction.category_name
        if not category_name:
            category_name = self.default_tx_category_name
        category_id = await self._get_category_id(
            user_id, category_name, session
        )
        transaction_to_create = self.creation_in_db_schema(
            amount=transaction.amount,
            description=transaction.description,
            date=transaction.date,
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
        transaction_update_obj: STransactionUpdatePartial,
        session: AsyncSession,
    ) -> STransactionResponse:
        transaction = await self.tx_repo.get_transaction_with_category(
            session,
            transaction_id,
        )
        if not transaction or transaction.user_id != user_id:
            raise TransactionNotFound

        transaction_to_update = self.update_partial_in_db_schema(
            amount=transaction_update_obj.amount,
            description=transaction_update_obj.description,
            date=transaction_update_obj.date,
        )

        new_cat_name = transaction_update_obj.category_name
        if new_cat_name:
            new_cat_name = new_cat_name.strip()
            if new_cat_name != transaction.category.category_name:
                new_category = await self.tx_categories_repo.get_category(
                    session=session,
                    user_id=user_id,
                    category_name=new_cat_name,
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
    ) -> STransactionResponse:
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

    async def delete_transaction(
        self,
        transaction_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> None:
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
        category = await self.tx_categories_repo.get_category(
            session=session,
            user_id=user_id,
            category_name=category_name,
        )
        if not category:
            raise CategoryNotFound
        return category.id

    async def get_transactions(
        self,
        session: AsyncSession,
        user_id: int,
        categories_params: list[SCategoryQueryParams],
        amount_params: SAmountRange | None = None,
        search_term: str | None = None,
        datetime_range: SDatetimeRange | None = None,
        sort_params: STransactionsSortParams | None = None,
    ) -> list[STransactionResponse]:
        categories_ids = await self._extract_category_ids(
            session=session,
            user_id=user_id,
            categories_params=categories_params,
        )

        if sort_params:
            parsed_sort_params = parse_sort_params_for_query(sort_params)
        else:
            parsed_sort_params = None

        transactions = await self.tx_repo.get_transactions_from_db(
            session=session,
            user_id=user_id,
            categories_ids=categories_ids if categories_ids else None,
            sort_params=parsed_sort_params,
            min_amount=amount_params.min_amount if amount_params else None,
            max_amount=amount_params.max_amount if amount_params else None,
            description_search_term=search_term,
            datetime_from=datetime_range.start if datetime_range else None,
            datetime_to=datetime_range.end if datetime_range else None,
        )
        result = []
        for transaction in transactions:
            transaction_out = self.out_schema(
                amount=transaction.amount,
                category_name=transaction.category.category_name,
                description=transaction.description,
                date=transaction.date,
                id=transaction.id,
            )
            result.append(transaction_out)
        return result

    async def get_summary(
        self,
        session: AsyncSession,
        user_id: int,
        categories_params: list[SCategoryQueryParams],
        amount_params: SAmountRange | None = None,
        search_term: str | None = None,
        datetime_range: SDatetimeRange | None = None,
    ) -> list[STransactionsSummary]:
        categories_ids = await self._extract_category_ids(
            session=session,
            user_id=user_id,
            categories_params=categories_params,
        )

        transactions = await self.tx_repo.get_transactions_from_db(
            session=session,
            user_id=user_id,
            categories_ids=categories_ids if categories_ids else None,
            min_amount=amount_params.min_amount if amount_params else None,
            max_amount=amount_params.max_amount if amount_params else None,
            description_search_term=search_term,
            datetime_from=datetime_range.start if datetime_range else None,
            datetime_to=datetime_range.end if datetime_range else None,
        )
        tx_out = []
        for transaction in transactions:
            transaction_out = self.out_schema(
                amount=transaction.amount,
                category_name=transaction.category.category_name,
                description=transaction.description,
                date=transaction.date,
                id=transaction.id,
            )
            tx_out.append(transaction_out)

        summary = self._summarize(tx_out)
        summary = self._sort_summarize(summary)

        return summary

    @staticmethod
    def _summarize(
        transactions: list[STransactionResponse],
    ) -> list[STransactionsSummary]:
        summary: defaultdict[str, int] = defaultdict(int)
        for transaction in transactions:
            if transaction.category_name:
                summary[transaction.category_name] += transaction.amount

        summary_out = []
        for category_name, amount in summary.items():
            summary_out.append(
                STransactionsSummary(
                    category_name=category_name,
                    amount=amount,
                )
            )
        return summary_out

    @staticmethod
    def _sort_summarize(
        summary: list[STransactionsSummary],
    ) -> list[STransactionsSummary]:
        summary.sort(key=lambda t: t.amount, reverse=True)
        return summary

    async def _extract_category_ids(
        self,
        session: AsyncSession,
        user_id: int,
        categories_params: list[SCategoryQueryParams],
    ) -> list[int]:
        category_ids = set()
        for cat_params in categories_params:
            if cat_params.category_name and cat_params.category_id is None:
                category = await self.tx_categories_repo.get_category(
                    session=session,
                    user_id=user_id,
                    category_name=cat_params.category_name,
                )
                if not category:
                    raise CategoryNotFound
                cat_params.category_id = category.id
            category_ids.add(cat_params.category_id)
        return list(category_ids)
