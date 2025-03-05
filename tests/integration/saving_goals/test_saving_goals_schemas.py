from contextlib import nullcontext
from datetime import date
from typing import ContextManager

import pytest
from pydantic import ValidationError

from app.schemas.saving_goals_schemas import SSavingGoalBase


@pytest.mark.parametrize(
    (
        "name",
        "description",
        "start_date",
        "target_date",
        "expected_name",
        "expected_descriptions",
        "expectation",
    ),
    [
        (
            "name",
            "description",
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
        (
            "name",
            "description",
            date(2025, 12, 1),
            date(2025, 1, 1),
            "name",
            "description",
            pytest.raises(ValidationError),
        ),
        (
            "     name    ",
            " description ",
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
        (
            "name ",
            " description",
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
        (
            "name ",
            " description",
            None,
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
    ]
)
def test_SSavingGoalBase_schema(
    name: str,
    description: str,
    start_date: date,
    target_date: date,
    expected_name: str,
    expected_descriptions: str,
    expectation: ContextManager,
):
    with expectation:
        goal = SSavingGoalBase(
            name=name,
            description=description,
            current_amount=0,
            target_amount=100,
            start_date=start_date,
            target_date=target_date,
        )
        assert goal.name == expected_name
        assert goal.description == expected_descriptions
