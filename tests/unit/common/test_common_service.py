from typing import Sequence

import pytest

from app.schemas.common_schemas import SPagination
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
