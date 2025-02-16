from fastapi import Query

from app.schemas.pagination_schemas import SPagination


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size limit"),
) -> SPagination:
    return SPagination(
        page=page,
        page_size=page_size,
    )
