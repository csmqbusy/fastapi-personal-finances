from typing import Sequence

import pandas as pd
from pydantic import BaseModel

from app.schemas.common_schemas import SPagination, SSortParamsBase, SortParam


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


def make_csv_from_pydantic_models(data: list[BaseModel]) -> str:
    df = pd.DataFrame([row.model_dump() for row in data])
    return df.to_csv(index=False)

