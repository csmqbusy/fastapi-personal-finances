import re
import uuid
from random import randint
from typing import Sequence, Type

import pytest
from pydantic import BaseModel

from app.schemas.common_schemas import SortParam, SPagination
from app.schemas.transactions_schemas import STransactionsSortParams
from app.services.common_service import (
    apply_pagination,
    get_filename_with_utc_datetime,
    make_csv_from_pydantic_models,
    parse_sort_params_for_query,
)


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
    ],
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
    ],
)
def test_parse_sort_params_for_query(
    sort_params: STransactionsSortParams,
    expected_result: list[SortParam],
):
    result = parse_sort_params_for_query(sort_params)
    assert result == expected_result


class ModelForTest(BaseModel):
    name: str
    age: int


@pytest.mark.parametrize(
    "pydantic_model, objects_qty",
    [
        (ModelForTest, 10),
        (ModelForTest, 500),
        (ModelForTest, 10000),
        (ModelForTest, 0),
    ],
)
def test_make_csv_from_pydantic_models(
    pydantic_model: Type[BaseModel],
    objects_qty: int,
    avg_row_length: int = 39,
):
    data = []
    for _ in range(objects_qty):
        obj = {
            "name": str(uuid.uuid4()),
            "age": randint(1, 100),
        }
        data.append(pydantic_model.model_validate(obj))

    result = make_csv_from_pydantic_models(data)
    assert type(result) is str
    assert len(result) >= objects_qty * avg_row_length


@pytest.mark.parametrize(
    "prefix, filetype",
    [
        ("prefix", "csv"),
        ("p", "anyfiletype"),
        ("", "py"),
    ],
)
def test_get_filename_with_utc_datetime(
    prefix: str,
    filetype: str,
    regular_expression: str = r"_\d{8}_\d{6}.",
):
    pattern = re.compile(rf"{prefix}{regular_expression}{filetype}")
    result = get_filename_with_utc_datetime(prefix, filetype)
    assert type(result) is str
    assert re.match(pattern, result) is not None
