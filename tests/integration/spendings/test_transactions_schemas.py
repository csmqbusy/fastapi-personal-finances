import pytest

from app.schemas.transactions_schemas import (
    STransactionsSortParams,
)


@pytest.mark.parametrize(
    "sort_params, expected_result",
    [
        (
            ["id", "date", "-category_name"],
            ["id", "date", "-category_name"],
        ),
        (
            ["-id", "-date", "-category_name"],
            ["-id", "-date", "-category_name"],
        ),
        (
            ["--id", "--date", "-category_name"],
            ["-id", "-date", "-category_name"],
        ),
        (
            ["-incorrect", "--date", "-category_name_"],
            ["-date"],
        ),
        (
            ["-incorrect", "--d-ate", "-category_name_"],
            [],
        ),
    ],
)
def test_STransactionsSortParams_schema(
    sort_params: list[str],
    expected_result: list[str],
):
    schema = STransactionsSortParams(sort_by=sort_params)
    assert schema.sort_by == expected_result
