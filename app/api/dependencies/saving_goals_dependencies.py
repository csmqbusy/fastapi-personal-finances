from datetime import date

from fastapi import Query

from app.schemas.common_schemas import SAmountRange, SDateRange
from app.schemas.saving_goals_schemas import SGoalsSortParams


def get_start_date_range(
    start_date_from: date = Query(None, description="Date included"),
    start_date_to: date = Query(None, description="Date included")
) -> SDateRange:
    return SDateRange(
        start=start_date_from,
        end=start_date_to,
    )


def get_target_date_range(
    target_date_from: date = Query(None, description="Date included"),
    target_date_to: date = Query(None, description="Date included")
) -> SDateRange:
    return SDateRange(
        start=target_date_from,
        end=target_date_to,
    )


def get_end_date_range(
    end_date_from: date = Query(None, description="Date included"),
    end_date_to: date = Query(None, description="Date included")
) -> SDateRange:
    return SDateRange(
        start=end_date_from,
        end=end_date_to,
    )


def get_goals_sort_params(
    sort_params: list[str] | None = Query(None, description="`-` is desc")
) -> SGoalsSortParams | None:
    if sort_params is not None:
        return SGoalsSortParams(sort_by=sort_params)
    return None


def get_current_amount_range(
    min_current_amount: int | None = Query(None, description="Value included"),
    max_current_amount: int | None = Query(None, description="Value included"),
) -> SAmountRange:
    return SAmountRange(
        min_amount=min_current_amount,
        max_amount=max_current_amount,
    )


def get_target_amount_range(
    min_target_amount: int | None = Query(None, description="Value included"),
    max_target_amount: int | None = Query(None, description="Value included"),
) -> SAmountRange:
    return SAmountRange(
        min_amount=min_target_amount,
        max_amount=max_target_amount,
    )
