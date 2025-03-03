from datetime import date

from fastapi import Query

from app.schemas.common_schemas import SDateRange


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

