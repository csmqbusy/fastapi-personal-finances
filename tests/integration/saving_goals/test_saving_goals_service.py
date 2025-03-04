from contextlib import nullcontext
from datetime import date
from typing import ContextManager

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.saving_goals_exceptions import (
    GoalNotFound,
    GoalCurrentAmountInvalid,
)
from app.repositories import user_repo
from app.schemas.saving_goals_schemas import (
    SSavingGoalCreate,
    SSavingGoalUpdatePartial,
    GoalStatus,
)
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "create_user",
        "new_name",
        "new_description",
        "new_current_amount",
        "new_target_amount",
        "new_start_date",
        "new_expected_start_date",
        "new_target_date",
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
            None,
            "Very good laptop",
            15000,
            190000,
            None,
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
            date.fromisoformat("2026-01-01"),
            date.fromisoformat("2026-01-01"),
            date.fromisoformat("2025-06-20"),
            pytest.raises(ValidationError),
        ),
        (
            False,
            "Macbook Pro",
            "Good laptop",
            200001,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            pytest.raises(ValidationError),
        ),
    ]
)
async def test_update_goal(
    db_session: AsyncSession,
    create_user: bool,
    new_name: str | None,
    new_description: str | None,
    new_current_amount: int | None,
    new_target_amount: int | None,
    new_start_date: date | None,
    new_expected_start_date: date | None,
    new_target_date: date | None,
    expectation: ContextManager,
):
    mock_user_username = "40Messi"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    goal = SSavingGoalCreate(
        name="name",
        current_amount=1234567,
        target_amount=1234567890,
        target_date=date.today(),
    )
    created_goal = await saving_goals_service.set_goal(
        session=db_session,
        goal=goal,
        user_id=user.id,
    )
    assert created_goal is not None
    assert created_goal.name != new_name
    assert created_goal.description != new_description
    assert created_goal.current_amount != new_current_amount
    assert created_goal.target_amount != new_target_amount
    assert created_goal.start_date != new_expected_start_date
    assert created_goal.target_date != new_target_date

    with expectation:
        goal_update_obj = SSavingGoalUpdatePartial(
            name=new_name,
            description=new_description,
            current_amount=new_current_amount,
            target_amount=new_target_amount,
            start_date=new_start_date,
            target_date=new_target_date,
        )
        updated_goal = await saving_goals_service.update_goal(
            goal_id=created_goal.id,
            user_id=user.id,
            goal_update_obj=goal_update_obj,
            session=db_session,
        )
        assert updated_goal is not None
        if new_name:
            assert updated_goal.name == goal_update_obj.name
        if new_description:
            assert updated_goal.description == goal_update_obj.description
        if new_current_amount:
            assert updated_goal.current_amount == goal_update_obj.current_amount
        if new_target_amount:
            assert updated_goal.target_amount == goal_update_obj.target_amount
        if new_start_date and new_expected_start_date:
            assert updated_goal.start_date == new_expected_start_date
        if new_target_date:
            assert updated_goal.target_date == goal_update_obj.target_date


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
        "wrong_user_id",
        "wrong_goal_id",
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
            9999,
            None,
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
        ),
    ]
)
async def test_get_goal_progress(
    db_session: AsyncSession,
    create_user: bool,
    name: str,
    description: str,
    current_amount: int,
    target_amount: int,
    start_date: date,
    expected_start_date: date,
    target_date: date,
    wrong_user_id: int | None,
    wrong_goal_id: int | None,
    expectation: ContextManager,
):
    mock_user_username = "50Messi"
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
        goal_progress = await saving_goals_service.get_goal_progress(
            goal_id=wrong_goal_id or created_goal.id,
            user_id=wrong_user_id or user.id,
            session=db_session,
        )
        assert goal_progress is not None
        assert goal_progress.current_amount == goal.current_amount
        assert goal_progress.target_amount == goal.target_amount
        assert goal_progress.rest_amount == goal.target_amount - goal.current_amount
        assert 0 <= goal_progress.percentage_progress <= 100
        assert goal_progress.days_left is not None
        assert goal_progress.expected_daily_payment is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "create_user",
        "name",
        "current_amount",
        "target_amount",
        "payment",
        "target_date",
        "wrong_user_id",
        "wrong_goal_id",
        "expected_status",
        "expected_current_amount",
        "expectation",
    ),
    [
        (
            True,
            "Macbook Pro",
            0,
            200000,
            20000,
            date.fromisoformat("2025-03-01"),
            None,
            None,
            GoalStatus.IN_PROGRESS,
            20000,
            nullcontext(),
        ),
        (
            False,
            "Macbook Pro",
            0,
            200000,
            200000,
            date.fromisoformat("2025-03-01"),
            None,
            None,
            GoalStatus.COMPLETED,
            200000,
            nullcontext(),
        ),
        (
            False,
            "Macbook Pro",
            10000,
            200000,
            -10001,
            date.fromisoformat("2025-03-01"),
            None,
            None,
            GoalStatus.IN_PROGRESS,
            10000,
            pytest.raises(GoalCurrentAmountInvalid),
        ),
        (
            False,
            "Macbook Pro",
            10000,
            200000,
            1000,
            date.fromisoformat("2025-03-01"),
            9999,
            None,
            GoalStatus.IN_PROGRESS,
            10000,
            pytest.raises(GoalNotFound),
        ),
        (
            False,
            "Macbook Pro",
            10000,
            200000,
            1000,
            date.fromisoformat("2025-03-01"),
            None,
            9999,
            GoalStatus.IN_PROGRESS,
            10000,
            pytest.raises(GoalNotFound),
        ),
    ]
)
async def test_update_current_amount(
    db_session: AsyncSession,
    create_user: bool,
    name: str,
    current_amount: int,
    target_amount: int,
    payment: int,
    target_date: date,
    wrong_user_id: int | None,
    wrong_goal_id: int | None,
    expected_status: GoalStatus,
    expected_current_amount: int,
    expectation: ContextManager,
):
    mock_user_username = "60Messi"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    goal = SSavingGoalCreate(
        name=name,
        current_amount=current_amount,
        target_amount=target_amount,
        target_date=target_date,
    )
    created_goal = await saving_goals_service.set_goal(
        session=db_session,
        goal=goal,
        user_id=user.id,
    )
    assert created_goal is not None

    with expectation:
        updated_goal = await saving_goals_service.update_current_amount(
            goal_id=wrong_goal_id or created_goal.id,
            user_id=wrong_user_id or user.id,
            payment=payment,
            session=db_session,
        )
        assert updated_goal is not None
        assert updated_goal.current_amount == expected_current_amount
