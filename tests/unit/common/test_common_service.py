from typing import Sequence

import pytest

import app.services
from app.schemas.common_schemas import SPagination, SortParam
from app.schemas.transactions_schemas import STransactionsSortParams
from app.services.common_service import apply_pagination


@pytest.mark.parametrize(
    "data, pagination, expected_result",
    [
        (
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            SPagination(page=1, page_size=5),
            [1, 2, 3, 4, 5],
        ),
        (
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            SPagination(page=2, page_size=5),
            [6, 7, 8, 9, 10],
        ),
        (
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            SPagination(page=1000, page_size=5),
            [],
        ),
        (
            (1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
            SPagination(page=5, page_size=2),
            (9, 10),
        ),
        (
            "abcdefg",
            SPagination(page=0, page_size=2),
            "",
        ),
        (
            "abcdefg",
            SPagination(page=1000, page_size=20),
            "",
        ),
    ]
)
def test_apply_pagination(
    data: Sequence,
    pagination: SPagination,
    expected_result: Sequence,
):
    result = apply_pagination(data, pagination)
    assert type(result) is type(expected_result)
    assert result == expected_result


@pytest.mark.parametrize(
    "sort_params, expected_result",
    [
        (
            STransactionsSortParams(
                sort_by=[
                    "id",
                    "date",
                    "-category_name",
                ],
            ),
            [
                SortParam(order_by="id", order_direction="asc"),
                SortParam(order_by="date", order_direction="asc"),
                SortParam(order_by="category_name", order_direction="desc"),
            ],
        ),
        (
            STransactionsSortParams(
                sort_by=[
                    "-id",
                    "date",
                    "-category_name",
                    "some non existent field",
                ],
            ),
            [
                SortParam(order_by="id", order_direction="desc"),
                SortParam(order_by="date", order_direction="asc"),
                SortParam(order_by="category_name", order_direction="desc"),
            ],
        ),
        (
            STransactionsSortParams(
                sort_by=[
                    "-id_non_exist",
                    "date_non_exist",
                    "-category_name_non_exist",
                    "some_non_exist",
                ],
            ),
            None,
        ),
        (
            STransactionsSortParams(
                sort_by=[],
            ),
            None,
        ),
    ]
)
def test_parse_sort_params_for_query(
    sort_params: STransactionsSortParams,
    expected_result: list[SortParam],
):

    result = app.services.common_service.parse_sort_params_for_query(sort_params)
    assert result == expected_result
