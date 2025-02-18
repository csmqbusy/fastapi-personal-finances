from datetime import date

from fastapi import Query

from app.schemas.date_range_schemas import SDateRange
from app.schemas.pagination_schemas import SPagination
from app.schemas.spendings_schemas import STransactionsQueryParams


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size limit"),
) -> SPagination:
    return SPagination(
        page=page,
        page_size=page_size,
    )


def get_date_range(
    date_from: date = Query(None, description="Date included"),
    date_to: date = Query(None, description="Date included")
) -> SDateRange:
    return SDateRange(
        start=date_from,
        end=date_to,
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
