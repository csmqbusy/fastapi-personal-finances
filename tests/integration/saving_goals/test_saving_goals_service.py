from contextlib import nullcontext
from datetime import date
from typing import ContextManager

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.saving_goals_exceptions import GoalNotFound
from app.repositories import user_repo
from app.schemas.saving_goals_schemas import SSavingGoalCreate
from app.services import saving_goals_service
from tests.integration.helpers import add_mock_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "create_user",
        "name",
        "description",
        "current_amount",
        "target_amount",
        "start_date",
        "expected_start_date",
        "target_date",
        "expectation",
    ),
    [
        (
            True,
            "Macbook Pro",
            "Good laptop",
            0,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            nullcontext(),
        ),
        (
            False,
            "Macbook Pro",
            None,
            0,
            200000,
            None,
            date.today(),
            date.fromisoformat("2025-06-20"),
            nullcontext(),
        ),
        (
            False,
            "Macbook Pro",
            None,
            0,
            200000,
            date.fromisoformat("2026-01-01"),
            date.fromisoformat("2026-01-01"),
            date.fromisoformat("2025-06-20"),
            pytest.raises(ValidationError),
        ),
        (
            False,
            None,
            None,
            0,
            200000,
            None,
            date.today(),
            date.fromisoformat("2025-06-20"),
            pytest.raises(ValidationError),
        ),
    ]
)
async def test_set_goal(
    db_session: AsyncSession,
    create_user: bool,
    name: str,
    description: str,
    current_amount: int,
    target_amount: int,
    start_date: date,
    expected_start_date: date,
    target_date: date,
    expectation: ContextManager,
):
    mock_user_username = "10Messi"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    with expectation:
        goal = SSavingGoalCreate(
            name=name,
            description=description,
            current_amount=current_amount,
            target_amount=target_amount,
            start_date=start_date,
            target_date=target_date,
        )
        created_goal = await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )
        assert created_goal is not None
        assert created_goal.name == goal.name
        assert created_goal.description == goal.description
        assert created_goal.current_amount == goal.current_amount
        assert created_goal.target_amount == goal.target_amount
        assert created_goal.start_date == expected_start_date
        assert created_goal.target_date == goal.target_date


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "create_user",
        "name",
        "description",
        "current_amount",
        "target_amount",
        "start_date",
        "expected_start_date",
        "target_date",
        "wrong_goal_id",
        "wrong_user_id",
        "expectation",
    ),
    [
        (
            True,
            "Macbook Pro",
            "Good laptop",
            0,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            None,
            None,
            nullcontext(),
        ),
        (
            False,
            "Macbook Pro",
            "Good laptop",
            0,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            None,
            9999,
            pytest.raises(GoalNotFound),
        ),
        (
            False,
            "Macbook Pro",
            "Good laptop",
            0,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            7777,
            None,
            pytest.raises(GoalNotFound),
        ),
    ]
)
async def test_get_goal(
    db_session: AsyncSession,
    create_user: bool,
    name: str,
    description: str,
    current_amount: int,
    target_amount: int,
    start_date: date,
    expected_start_date: date,
    target_date: date,
    wrong_goal_id: int | None,
    wrong_user_id: int | None,
    expectation: ContextManager,
):
    mock_user_username = "20Messi"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    goal = SSavingGoalCreate(
        name=name,
        description=description,
        current_amount=current_amount,
        target_amount=target_amount,
        start_date=start_date,
        target_date=target_date,
    )
    created_goal = await saving_goals_service.set_goal(
        session=db_session,
        goal=goal,
        user_id=user.id,
    )

    with expectation:
        goal_from_db = await saving_goals_service.get_goal(
            goal_id=wrong_goal_id or created_goal.id,
            user_id=wrong_user_id or user.id,
            session=db_session,
        )
        assert goal_from_db is not None
        assert goal_from_db.name == goal.name
        assert goal_from_db.description == goal.description
        assert goal_from_db.current_amount == goal.current_amount
        assert goal_from_db.target_amount == goal.target_amount
        assert goal_from_db.start_date == expected_start_date
        assert goal_from_db.target_date == goal.target_date



@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "create_user",
        "name",
        "description",
        "current_amount",
        "target_amount",
        "start_date",
        "expected_start_date",
        "target_date",
        "wrong_goal_id",
        "wrong_user_id",
        "expectation",
        "after_delete_expectation",
    ),
    [
        (
            True,
            "Macbook Pro",
            "Good laptop",
            0,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            None,
            None,
            nullcontext(),
            pytest.raises(GoalNotFound),
        ),
        (
            False,
            "Macbook Pro",
            "Good laptop",
            0,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            None,
            9999,
            pytest.raises(GoalNotFound),
            pytest.raises(GoalNotFound),
        ),
        (
            False,
            "Macbook Pro",
            "Good laptop",
            0,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            7777,
            None,
            pytest.raises(GoalNotFound),
            pytest.raises(GoalNotFound),
        ),
    ]
)
async def test_delete_goal(
    db_session: AsyncSession,
    create_user: bool,
    name: str,
    description: str,
    current_amount: int,
    target_amount: int,
    start_date: date,
    expected_start_date: date,
    target_date: date,
    wrong_goal_id: int | None,
    wrong_user_id: int | None,
    expectation: ContextManager,
    after_delete_expectation: ContextManager,
):
    mock_user_username = "30Messi"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    goal = SSavingGoalCreate(
        name=name,
        description=description,
        current_amount=current_amount,
        target_amount=target_amount,
        start_date=start_date,
        target_date=target_date,
    )
    created_goal = await saving_goals_service.set_goal(
        session=db_session,
        goal=goal,
        user_id=user.id,
    )
    assert created_goal is not None

    with expectation:
        await saving_goals_service.delete_goal(
            goal_id=wrong_goal_id or created_goal.id,
            user_id=wrong_user_id or user.id,
            session=db_session,
        )
        with after_delete_expectation:
            await saving_goals_service.get_goal(
                goal_id=wrong_goal_id or created_goal.id,
                user_id=wrong_user_id or user.id,
                session=db_session,
            )
