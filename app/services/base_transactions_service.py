import calendar
from collections import defaultdict
from typing import Any, Sequence, Type

from aio_pika import connect_robust
from aio_pika.patterns import RPC
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.categories_exceptions import (
    CategoryNotFound,
)
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.repositories import (
    BaseCategoriesRepository,
    BaseTransactionsRepository,
)
from app.schemas.common_schemas import (
    SAmountRange,
    SDatetimeRange,
)
from app.schemas.transaction_category_schemas import SCategoryQueryParams
from app.schemas.transactions_schemas import (
    BasePeriodTransactionsSummary,
    DayTransactionsSummary,
    DayTransactionsSummaryCSV,
    MonthTransactionsSummary,
    MonthTransactionsSummaryCSV,
    STransactionCreate,
    STransactionCreateInDB,
    STransactionResponse,
    STransactionsSortParams,
    STransactionsSummary,
    STransactionUpdatePartial,
    STransactionUpdatePartialInDB,
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
        category_id = await self._get_category_id(user_id, category_name, session)
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
        """
        Returns summary – the sum of transactions amount by category.
        """
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

    async def get_summary_chart(
        self,
        session: AsyncSession,
        user_id: int,
        categories_params: list[SCategoryQueryParams],
        chart_type: str | None = None,
        amount_params: SAmountRange | None = None,
        search_term: str | None = None,
        datetime_range: SDatetimeRange | None = None,
    ) -> bytes:
        summary = await self.get_summary(
            session=session,
            user_id=user_id,
            categories_params=categories_params,
            amount_params=amount_params,
            search_term=search_term,
            datetime_range=datetime_range,
        )
        categories = []
        amounts = []
        for s in summary:
            categories.append(s.category_name)
            amounts.append(s.amount)

        result = await self.rpc_call(
            "create_simple_chart",
            dict(
                values=amounts,
                labels=categories,
                chart_type=chart_type or "barplot",
            ),
        )

        return result

    async def get_annual_summary(
        self,
        session: AsyncSession,
        user_id: int,
        year: int,
    ) -> list[MonthTransactionsSummary]:
        """
        Returns an annual summary divided by month and category.
        """
        annual_summary = await self.tx_repo.get_annual_summary_from_db(
            session=session,
            year=year,
            user_id=user_id,
        )
        annual_by_month_dict = defaultdict(list)
        for elem in list(annual_summary):
            month = elem[2]
            annual_by_month_dict[month].append(
                STransactionsSummary(amount=elem[0], category_name=elem[1])
            )

        annual_by_month_schema = []
        for k, v in annual_by_month_dict.items():
            annual_by_month_schema.append(
                MonthTransactionsSummary(
                    month_number=int(k),
                    total_amount=sum(cat.amount for cat in v),
                    summary=v,
                )
            )
        return annual_by_month_schema

    async def get_annual_summary_chart(
        self,
        session: AsyncSession,
        user_id: int,
        year: int,
        transactions_type: str,
        split_by_category: bool,
    ):
        annual_summary = await self.get_annual_summary(session, user_id, year)

        months = list(range(1, 13))
        amounts = [0] * len(months)
        rpc_params: dict[str, Any] = {
            "title": f"{transactions_type.capitalize()} {year}",
            "xlabel": "Month",
            "width": 9,
            "height": 5,
        }
        if split_by_category:
            categories = self._get_categories_from_summary(annual_summary)
            prepared_data = self._prepare_data_for_chart_with_categories_split(
                annual_summary, categories
            )
            rpc_method_name = "create_annual_chart_with_categories"
            rpc_params.update(dict(data=prepared_data, categories=categories))

        else:
            total_amounts = amounts.copy()
            for record in annual_summary:
                total_amounts[record.month_number - 1] = record.total_amount
            rpc_method_name = "create_simple_bar_chart"
            rpc_params.update(dict(values=total_amounts))

        result = await self.rpc_call(rpc_method_name, rpc_params)
        return result

    async def get_monthly_summary(
        self,
        session: AsyncSession,
        user_id: int,
        year: int,
        month: int,
    ) -> list[DayTransactionsSummary]:
        """
        Returns a monthly summary divided by day and category.
        """
        monthly_summary = await self.tx_repo.get_monthly_summary_from_db(
            session=session,
            year=year,
            user_id=user_id,
            month=month,
        )
        monthly_by_day_dict = defaultdict(list)
        for elem in list(monthly_summary):
            day = elem[2]
            monthly_by_day_dict[day].append(
                STransactionsSummary(amount=elem[0], category_name=elem[1])
            )

        monthly_by_day_schema = []
        for k, v in monthly_by_day_dict.items():
            monthly_by_day_schema.append(
                DayTransactionsSummary(
                    day_number=int(k),
                    total_amount=sum(cat.amount for cat in v),
                    summary=v,
                )
            )
        return monthly_by_day_schema

    async def get_monthly_summary_chart(
        self,
        session: AsyncSession,
        user_id: int,
        year: int,
        month: int,
        transactions_type: str,
        split_by_category: bool,
    ):
        monthly_summary = await self.get_monthly_summary(
            session, user_id, year, month
        )

        month_name = calendar.month_name[month]
        days_in_month = calendar.monthrange(year, month)[1]
        amounts = [0] * days_in_month
        rpc_params: dict[str, Any] = {
            "title": f"{transactions_type.capitalize()} {month_name} {year}",
            "xlabel": "Day",
            "width": 10,
            "height": 5,
        }
        if split_by_category:
            categories = self._get_categories_from_summary(monthly_summary)
            prepared_data = self._prepare_data_for_chart_with_categories_split(
                monthly_summary, categories
            )

            rpc_method_name = "create_monthly_chart_with_categories"
            rpc_params.update(
                dict(
                    data=prepared_data,
                    categories=categories,
                    days_in_month=days_in_month,
                )
            )
        else:
            total_amounts = amounts.copy()
            for record in monthly_summary:  # type: DayTransactionsSummary
                total_amounts[record.day_number - 1] = record.total_amount
            rpc_method_name = "create_simple_bar_chart"
            rpc_params.update(dict(values=total_amounts))

        result = await self.rpc_call(rpc_method_name, rpc_params)
        return result

    @staticmethod
    def _get_categories_from_summary(
        summary: Sequence[BasePeriodTransactionsSummary],
    ) -> set:
        """
        Extracts all categories that occur in summary.
        """
        categories = set()
        for record in summary:
            for item in record.summary:
                categories.add(item.category_name)
        return categories

    @staticmethod
    def _prepare_data_for_chart_with_categories_split(
        summary: Sequence[BasePeriodTransactionsSummary],
        categories: set,
    ) -> list[dict[str, Any]]:
        """
        Prepares data in a json-compatible format.
        Adds data about all categories to each period.

        Output example:
        [
            {'Food': 70, 'Clothes': 0, 'month_number': 1, 'total_amount': 70},
            {'Food': 0, 'Clothes': 60, 'month_number': 2, 'total_amount': 60},
            {'Food': 10, 'Clothes': 40, 'month_number': 3, 'total_amount': 50},
        ]
        """
        transformed_data = []
        for record in summary:
            period_data = record.model_dump(exclude={"summary"})

            for category in categories:
                period_data[category] = 0

            for item in record.summary:
                period_data[item.category_name] = item.amount

            transformed_data.append(period_data)
        return transformed_data

    @staticmethod
    async def rpc_call(method_name: str, params: dict[str, Any]) -> Any:
        connection = await connect_robust(settings.broker.url)
        async with connection:
            channel = await connection.channel()
            rpc = await RPC.create(channel)
            return await rpc.call(
                method_name=method_name,
                kwargs=params,
            )

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
        """
        Retrieves category IDs from the list of SCategoryQueryParams objects,
        which may contain category names.
        """
        category_ids: set[int] = set()
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
            if cat_params.category_id:
                category_ids.add(cat_params.category_id)
        return list(category_ids)

    @staticmethod
    def prepare_annual_summary_for_csv(
        period_summary: list[MonthTransactionsSummary],
    ) -> list[MonthTransactionsSummaryCSV]:
        """
        Converts a nested JSON object to a format suitable for CSV,
        when the bulk JSON data is repeated in each nested object.
        """
        result = []
        for record in period_summary:
            for summ in record.summary:
                data = {
                    "category_name": summ.category_name,
                    "amount": summ.amount,
                    "total_amount": record.total_amount,
                    "month_number": record.month_number,
                }
                result.append(MonthTransactionsSummaryCSV.model_validate(data))
        return result

    @staticmethod
    def prepare_monthly_summary_for_csv(
        period_summary: list[DayTransactionsSummary],
    ) -> list[DayTransactionsSummaryCSV]:
        """
        Converts a nested JSON object to a format suitable for CSV,
        when the bulk JSON data is repeated in each nested object.
        """
        result = []
        for record in period_summary:
            for summ in record.summary:
                data = {
                    "category_name": summ.category_name,
                    "amount": summ.amount,
                    "total_amount": record.total_amount,
                    "day_number": record.day_number,
                }
                result.append(DayTransactionsSummaryCSV.model_validate(data))
        return result
