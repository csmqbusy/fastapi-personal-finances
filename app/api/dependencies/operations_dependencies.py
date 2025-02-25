from datetime import datetime

from fastapi import Query

from app.schemas.date_range_schemas import SDatetimeRange
from app.schemas.pagination_schemas import SPagination
from app.schemas.transactions_schemas import (
    STransactionsQueryParams,
    STransactionsSortParams,
    SAmountRange,
)


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Objects per page"),
) -> SPagination:
    return SPagination(
        page=page,
        page_size=page_size,
    )


def get_date_range(
    datetime_from: datetime = Query(None, description="Date included"),
    datetime_to: datetime = Query(None, description="Date included")
) -> SDatetimeRange:
    return SDatetimeRange(
        start=datetime_from,
        end=datetime_to,
    )


def get_transactions_query_params(
    category_id: int | None = Query(
        None,
        description=(
            "The priority way to identify a category. "
            "If there is conflicting information in category_id and "
            "category_name, category_id will be used."
        ),
    ),
    category_name: str | None = Query(
        None,
        description=(
            "Specify the category name if the id is unknown. "
            "Ignore the category_id parameter if you use category_name."
        ),
    ),
) -> STransactionsQueryParams:
    return STransactionsQueryParams(
        category_id=category_id,
        category_name=category_name,
    )


def get_transactions_sort_params(
    sort_params: list[str] | None = Query(None, description="`-` is desc")
) -> STransactionsSortParams:
    if sort_params is not None:
        return STransactionsSortParams(sort_by=sort_params)


def get_amount_range(
    min_amount: int | None = Query(None, description="Value included"),
    max_amount: int | None = Query(None, description="Value included"),
) -> SAmountRange:
    return SAmountRange(min_amount=min_amount, max_amount=max_amount)
