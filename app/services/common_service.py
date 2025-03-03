from typing import Sequence

from app.schemas.common_schemas import SPagination, SSortParamsBase
from app.schemas.transactions_schemas import SortParam


def apply_pagination(
    data: Sequence,
    pagination: SPagination,
):
    start = (pagination.page - 1) * pagination.page_size
    stop = pagination.page * pagination.page_size
    return data[start:stop]


def parse_sort_params_for_query(
    sort_params: SSortParamsBase,
) -> list[SortParam] | None:
    if sort_params.sort_by is None:
        return None

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

    return result if result else None
