from typing import Sequence

from app.schemas.common_schemas import SPagination


def apply_pagination(
    data: Sequence,
    pagination: SPagination,
):
    start = (pagination.page - 1) * pagination.page_size
    stop = pagination.page * pagination.page_size
    return data[start:stop]
