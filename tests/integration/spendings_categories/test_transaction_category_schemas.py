from contextlib import nullcontext
from typing import ContextManager

import pytest
from pydantic import ValidationError

from app.schemas.transaction_category_schemas import STransactionCategoryBase


@pytest.mark.parametrize(
    "category_name, valid_category_name, expectation",
    [
        (
            "Games",
            "Games",
            nullcontext(),
        ),
        (
            "     Games  ",
            "Games",
            nullcontext(),
        ),
        (
            "G@me7  ",
            "G@me7",
            nullcontext(),
        ),
        (
            " c",
            "c",
            nullcontext(),
        ),
        (
            "",
            None,
            pytest.raises(ValidationError),
        ),
        (
            " ",
            None,
            pytest.raises(ValidationError),
        ),
    ],
)
def test_STransactionCategoryBase_schema(
    category_name: str,
    valid_category_name: str | None,
    expectation: ContextManager,
):
    with expectation:
        obj = STransactionCategoryBase(category_name=category_name)
        assert valid_category_name == obj.category_name
