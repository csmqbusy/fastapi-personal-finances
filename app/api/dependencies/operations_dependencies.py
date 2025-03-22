from datetime import datetime

from fastapi import Query

from app.api.exceptions.operations_exceptions import CategoryInfoError
from app.schemas.common_schemas import (
    SAmountRange,
    SDatetimeRange,
    SPagination,
)
from app.schemas.transaction_category_schemas import SCategoryQueryParams
from app.schemas.transactions_schemas import (
    STransactionsSortParams,
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


def get_categories_params(
    category_id: list[int] | None = Query(
        None,
        description=(
            "Use only one way to send information about categories: "
            "category_id or category_name"
        ),
    ),
    category_name: list[str] | None = Query(
        None,
        description=(
            "Specify the category name if the id is unknown. "
            "Use only one way to send information about categories: "
            "category_id or category_name"
        ),
    ),
) -> list[SCategoryQueryParams]:
    if category_id and category_name:
        raise CategoryInfoError()

    if category_id:
        category_params = [
            SCategoryQueryParams(category_id=cat_id)
            for cat_id in category_id
        ]
    elif category_name:
        category_params = [
            SCategoryQueryParams(category_name=cat_name)
            for cat_name in category_name
        ]
    else:
        category_params = []

    return category_params


def get_transactions_sort_params(
    sort_params: list[str] | None = Query(None, description="`-` is desc")
) -> STransactionsSortParams | None:
    if sort_params is not None:
        return STransactionsSortParams(sort_by=sort_params)
    return None


def get_amount_range(
    min_amount: int | None = Query(None, description="Value included"),
    max_amount: int | None = Query(None, description="Value included"),
) -> SAmountRange:
    return SAmountRange(min_amount=min_amount, max_amount=max_amount)
