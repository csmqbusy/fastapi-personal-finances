from contextlib import nullcontext
from datetime import date
from typing import ContextManager

import pytest
from pydantic import ValidationError

from app.schemas.saving_goals_schemas import (
    SSavingGoalBase,
    SSavingGoalUpdatePartial,
)


@pytest.mark.parametrize(
    (
        "name",
        "description",
        "current_amount",
        "target_amount",
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
            0,
            100,
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
        (
            "name",
            "description",
            0,
            100,
            date(2025, 12, 1),
            date(2025, 1, 1),
            "name",
            "description",
            pytest.raises(ValidationError),
        ),
        (
            "name",
            "description",
            120,
            100,
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            pytest.raises(ValidationError),
        ),
        (
            "     name    ",
            " description ",
            0,
            100,
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
        (
            "name ",
            " description",
            0,
            100,
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
        (
            "name ",
            " description",
            0,
            100,
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
    current_amount: int,
    target_amount: int,
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
            current_amount=current_amount,
            target_amount=target_amount,
            start_date=start_date,
            target_date=target_date,
        )
        assert goal.name == expected_name
        assert goal.description == expected_descriptions



@pytest.mark.parametrize(
    (
        "name",
        "description",
        "current_amount",
        "target_amount",
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
            0,
            1000,
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
        (
            "name",
            "description",
            0,
            1000,
            date(2025, 12, 1),
            date(2025, 1, 1),
            "name",
            "description",
            pytest.raises(ValidationError),
        ),
        (
            "name",
            "description",
            10000,
            1000,
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            pytest.raises(ValidationError),
        ),
        (
            "   name",
            "description   ",
            1000,
            1000,
            date(2025, 1, 1),
            date(2025, 12, 1),
            "name",
            "description",
            nullcontext(),
        ),
    ]
)
def test_SSavingGoalUpdatePartial_schema(
    name: str,
    description: str,
    current_amount: int,
    target_amount: int,
    start_date: date,
    target_date: date,
    expected_name: str,
    expected_descriptions: str,
    expectation: ContextManager,
):
    with expectation:
        goal = SSavingGoalUpdatePartial(
            name=name,
            description=description,
            current_amount=current_amount,
            target_amount=target_amount,
            start_date=start_date,
            target_date=target_date,
        )
        assert goal.name == expected_name
        assert goal.description == expected_descriptions
