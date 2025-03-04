from contextlib import nullcontext
from datetime import date, timedelta
from typing import ContextManager

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.saving_goals_exceptions import (
    GoalNotFound,
    GoalCurrentAmountInvalid,
)
from app.repositories import user_repo
from app.schemas.common_schemas import SAmountRange, SDateRange
from app.schemas.saving_goals_schemas import (
    SSavingGoalCreate,
    SSavingGoalUpdatePartial,
    GoalStatus,
    SGoalsSortParams,
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
        "expected_status",
        "expected_end_date",
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
            GoalStatus.IN_PROGRESS,
            None,
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
            GoalStatus.IN_PROGRESS,
            None,
            nullcontext(),
        ),
        (
            False,
            "Macbook Pro",
            "Good laptop",
            200000,
            200000,
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-01-01"),
            date.fromisoformat("2025-06-20"),
            GoalStatus.COMPLETED,
            date.today(),
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
            GoalStatus.IN_PROGRESS,
            None,
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
            GoalStatus.IN_PROGRESS,
            None,
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
    expected_status: GoalStatus,
    expected_end_date: date | None,
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "current_amounts",
        "target_amounts",
        "current_amount_range",
        "target_amount_range",
        "expected_goals_qty",
    ),
    [
        (
            "70Messi1",
            [0, 500, 1000, 1500, 2000, 2500],
            [5000, 10000, 15000, 20000, 25000, 30000],
            SAmountRange(min_amount=0, max_amount=1500),
            SAmountRange(min_amount=5000, max_amount=15000),
            3,
        ),
        (
            "70Messi2",
            [0, 500, 1000, 1500, 2000, 2500],
            [5000, 10000, 15000, 20000, 25000, 30000],
            SAmountRange(min_amount=None, max_amount=None),
            SAmountRange(min_amount=None, max_amount=None),
            6,
        ),
        (
            "70Messi3",
            [0, 500, 1000, 1500, 2000, 2500],
            [5000, 10000, 15000, 20000, 25000, 30000],
            SAmountRange(min_amount=None, max_amount=2000),
            SAmountRange(min_amount=None, max_amount=20000),
            4,
        ),
        (
            "70Messi4",
            [0, 500, 1000, 1500, 2000, 2500],
            [5000, 10000, 15000, 20000, 25000, 30000],
            SAmountRange(min_amount=500, max_amount=None),
            SAmountRange(min_amount=30000, max_amount=None),
            1,
        ),
    ]
)
async def test_get_goals_all__with_amounts_range(
    db_session: AsyncSession,
    username: str,
    current_amounts: list[int],
    target_amounts: list[int],
    current_amount_range: SAmountRange,
    target_amount_range: SAmountRange,
    expected_goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for i in range(len(current_amounts)):
        goal = SSavingGoalCreate(
            name="mock",
            current_amount=current_amounts[i],
            target_amount=target_amounts[i],
            target_date=date.today() + timedelta(days=i),
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

    goals = await saving_goals_service.get_goals_all(
        session=db_session,
        user_id=user.id,
        current_amount_range=current_amount_range,
        target_amount_range=target_amount_range,

    )
    if current_amount_range.min_amount:
        current_min_amount = current_amount_range.min_amount
    else:
        current_min_amount = 0
    if current_amount_range.max_amount:
        current_max_amount = current_amount_range.max_amount
    else:
        current_max_amount = float("inf")
    if target_amount_range.min_amount:
        target_min_amount = target_amount_range.min_amount
    else:
        target_min_amount = 0
    if target_amount_range.max_amount:
        target_max_amount = target_amount_range.max_amount
    else:
        target_max_amount = float("inf")

    assert len(goals) == expected_goals_qty
    for goal in goals:
        assert current_min_amount <= goal.current_amount <= current_max_amount
        assert target_min_amount <= goal.target_amount <= target_max_amount


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "names",
        "descriptions",
        "name_search_term",
        "description_search_term",
        "expected_goals_qty",
    ),
    [
        (
            "80Messi1",
            ["TEXT", "text", " text ", "t3xT   "],
            [" some description", "description text", "my desc text", "desc"],
            "text",
            "description",
            2,
        ),
        (
            "80Messi2",
            ["TEXT", "text", " text ", "t3xT   "],
            [" some description", "description text", "my desc text", "desc"],
            "text",
            "desc",
            3,
        ),
        (
            "80Messi3",
            ["TEXT", "text", " text ", "t3xT   "],
            [" some description", "description text", "my desc text", "desc"],
            "T3XT",
            None,
            1,
        ),
        (
            "80Messi4",
            ["TEXT", "text", " text ", "t3xT   "],
            [" some description", "description text", "my desc text", "desc"],
            None,
            "desc ",
            1,
        ),
    ]
)
async def test_get_goals_all__with_search_terms(
    db_session: AsyncSession,
    username: str,
    names: list[str],
    descriptions: list[str],
    name_search_term: str | None,
    description_search_term: str | None,
    expected_goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for i in range(len(names)):
        goal = SSavingGoalCreate(
            name=names[i],
            description=descriptions[i],
            current_amount=0,
            target_amount=2000,
            target_date=date.today() + timedelta(days=i),
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

    goals = await saving_goals_service.get_goals_all(
        session=db_session,
        user_id=user.id,
        name_search_term=name_search_term,
        description_search_term=description_search_term,
    )

    assert len(goals) == expected_goals_qty
    for goal in goals:
        if name_search_term:
            assert name_search_term.lower() in goal.name.lower()
        if description_search_term:
            assert description_search_term.lower() in goal.description.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "start_dates",
        "target_dates",
        "start_date_range",
        "target_date_range",
        "expected_goals_qty",
    ),
    [
        (
            "90Messi1",
            [
                date(2025, 1, 1),
                date(2025, 2, 1),
                date(2025, 3, 1),
                date(2025, 4, 1),
                date(2025, 5, 1),
            ],
            [
                date(2025, 12, 27),
                date(2025, 12, 28),
                date(2025, 12, 29),
                date(2025, 12, 30),
                date(2025, 12, 31),
            ],
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            5,
        ),
        (
            "90Messi2",
            [
                date(2025, 1, 1),
                date(2025, 2, 1),
                date(2025, 3, 1),
                date(2025, 4, 1),
                date(2025, 5, 1),
            ],
            [
                date(2025, 12, 27),
                date(2025, 12, 28),
                date(2025, 12, 29),
                date(2025, 12, 30),
                date(2025, 12, 31),
            ],
            SDateRange(start=date(2025, 1, 1), end=date(2025, 3, 31)),
            SDateRange(start=date(2025, 12, 28), end=date(2025, 12, 31)),
            2,
        ),
        (
            "90Messi3",
            [
                date(2025, 1, 1),
                date(2025, 2, 1),
                date(2025, 3, 1),
                date(2025, 4, 1),
                date(2025, 5, 1),
            ],
            [
                date(2025, 12, 27),
                date(2025, 12, 28),
                date(2025, 12, 29),
                date(2025, 12, 30),
                date(2025, 12, 31),
            ],
            SDateRange(start=date(2025, 5, 1), end=date(2025, 12, 31)),
            None,
            1,
        ),
        (
            "90Messi4",
            [
                date(2025, 1, 1),
                date(2025, 2, 1),
                date(2025, 3, 1),
                date(2025, 4, 1),
                date(2025, 5, 1),
            ],
            [
                date(2025, 12, 27),
                date(2025, 12, 28),
                date(2025, 12, 29),
                date(2025, 12, 30),
                date(2025, 12, 31),
            ],
            None,
            SDateRange(start=date(2025, 12, 29), end=date(2025, 12, 31)),
            3,
        ),
    ]
)
async def test_get_goals_all__with_date_ranges(
    db_session: AsyncSession,
    username: str,
    start_dates: list[date],
    target_dates: list[date],
    start_date_range: SDateRange | None,
    target_date_range: SDateRange | None,
    expected_goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for i in range(len(start_dates)):
        goal = SSavingGoalCreate(
            name="mock",
            current_amount=0,
            target_amount=2000,
            start_date=start_dates[i],
            target_date=target_dates[i],
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

    goals = await saving_goals_service.get_goals_all(
        session=db_session,
        user_id=user.id,
        start_date_range=start_date_range,
        target_date_range=target_date_range,
    )

    assert len(goals) == expected_goals_qty
    for goal in goals:
        if start_date_range:
            assert start_date_range.start <= goal.start_date
            assert start_date_range.end >= goal.start_date
        if target_date_range:
            assert target_date_range.start <= goal.target_date
            assert target_date_range.end >= goal.target_date


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "goals_qty",
        "end_date_range",
        "expected_goals_qty",
    ),
    [
        (
            "100Messi1",
            5,
            SDateRange(start=date.today(), end=date.today()),
            5,
        ),
        (
            "100Messi2",
            5,
            SDateRange(start=date(2020, 1, 1), end=date(2023, 1, 1)),
            0,
        ),
    ]
)
async def test_get_goals_all__with_end_date_range(
    db_session: AsyncSession,
    username: str,
    goals_qty: int,
    end_date_range: SDateRange,
    expected_goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for i in range(goals_qty):
        goal = SSavingGoalCreate(
            name="mock",
            current_amount=1000,
            target_amount=1000,
            target_date=date(2030, 1, 1),
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

    goals = await saving_goals_service.get_goals_all(
        session=db_session,
        user_id=user.id,
        end_date_range=end_date_range,
    )

    assert len(goals) == expected_goals_qty
    for goal in goals:
        assert end_date_range.start <= goal.start_date
        assert end_date_range.end <= goal.start_date


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "current_amounts",
        "target_amounts",
        "status",
        "expected_goals_qty",
    ),
    [
        (
            "110Messi1",
            [100, 200, 300],
            [200, 400, 300],
            GoalStatus.IN_PROGRESS,
            2,
        ),
        (
            "110Messi2",
            [100, 200, 300],
            [200, 400, 300],
            GoalStatus.COMPLETED,
            1,
        ),
    ]
)
async def test_get_goals_all__with_status(
    db_session: AsyncSession,
    username: str,
    current_amounts: list[int],
    target_amounts: list[int],
    status: GoalStatus,
    expected_goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for i in range(len(current_amounts)):
        goal = SSavingGoalCreate(
            name="mock",
            current_amount=current_amounts[i],
            target_amount=target_amounts[i],
            target_date=date(2030, 1, 1),
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

    goals = await saving_goals_service.get_goals_all(
        session=db_session,
        user_id=user.id,
        status=status,
    )

    assert len(goals) == expected_goals_qty
    for goal in goals:
        assert goal.status == status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "current_amounts",
        "target_amounts",
        "current_amount_range",
        "target_amount_range",
        "names",
        "descriptions",
        "name_search_term",
        "description_search_term",
        "start_dates",
        "target_dates",
        "start_date_range",
        "target_date_range",
        "end_date_range",
        "status",
        "sort_params",
        "sorted_target_amounts",
        "expected_goals_qty",
    ),
    [
        (
            "120Messi1",
            [0, 1000, 2000, 3000, 4000],
            [5000, 15000, 10000, 20000, 30000],
            SAmountRange(min_amount=0, max_amount=3000),
            SAmountRange(min_amount=5000, max_amount=20000),
            ["TEXT", "TEXT", "text", " text ", "t3xT   "],
            [" some description", "description text", "my desc ", "desc", " "],
            "text",
            "desc",
            [
                date(2025, 1, 1),
                date(2025, 2, 1),
                date(2025, 3, 1),
                date(2025, 4, 1),
                date(2025, 5, 1),
            ],
            [
                date(2025, 12, 27),
                date(2025, 12, 28),
                date(2025, 12, 29),
                date(2025, 12, 30),
                date(2025, 12, 31),
            ],
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            None,
            GoalStatus.IN_PROGRESS,
            SGoalsSortParams(sort_by=["-target_amount", "-current_amount"]),
            [20000, 15000, 10000, 5000],
            4,
        ),
        (
            "120Messi2",
            [0, 1000, 3000, 3000, 4000],
            [5000, 10000, 3000, 20000, 30000],
            SAmountRange(min_amount=0, max_amount=3000),
            SAmountRange(min_amount=3000, max_amount=20000),
            ["TEXT", "TEXT", "text", " text ", "t3xT   "],
            [" some description", "description text", "my desc ", "desc", " "],
            "text",
            "desc",
            [
                date(2025, 1, 1),
                date(2025, 2, 1),
                date(2025, 3, 1),
                date(2025, 4, 1),
                date(2025, 5, 1),
            ],
            [
                date(2025, 12, 27),
                date(2025, 12, 28),
                date(2025, 12, 29),
                date(2025, 12, 30),
                date(2025, 12, 31),
            ],
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            SDateRange(start=date(2025, 12, 29), end=date(2025, 12, 31)),
            SDateRange(start=date.today(), end=date.today()),
            GoalStatus.COMPLETED,
            SGoalsSortParams(sort_by=["-target_amount", "-current_amount"]),
            [3000],
            1,
        ),
    ]
)
async def test_get_goals_all__with_all_filters(
    db_session: AsyncSession,
    username: str,
    current_amounts: list[int],
    target_amounts: list[int],
    current_amount_range: SAmountRange,
    target_amount_range: SAmountRange,
    names: list[str],
    descriptions: list[str],
    name_search_term: str,
    description_search_term: str,
    start_dates: list[date],
    target_dates: list[date],
    start_date_range: SDateRange,
    target_date_range: SDateRange,
    end_date_range: SDateRange | None,
    status: GoalStatus,
    sort_params: SGoalsSortParams,
    sorted_target_amounts: list[int],
    expected_goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for i in range(len(current_amounts)):
        goal = SSavingGoalCreate(
            name=names[i],
            description=descriptions[i],
            current_amount=current_amounts[i],
            target_amount=target_amounts[i],
            start_date=start_dates[i],
            target_date=target_dates[i],
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

    goals = await saving_goals_service.get_goals_all(
        session=db_session,
        user_id=user.id,
        current_amount_range=current_amount_range,
        target_amount_range=target_amount_range,
        name_search_term=name_search_term,
        description_search_term=description_search_term,
        start_date_range=start_date_range,
        target_date_range=target_date_range,
        end_date_range=end_date_range,
        status=status,
        sort_params=sort_params,
    )

    assert len(goals) == expected_goals_qty
    assert [g.target_amount for g in goals] == sorted_target_amounts


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
    ),
    [
        (
            "130Messi1",
        ),
    ]
)
async def test__complete_saving_goal(
    db_session: AsyncSession,
    username: str,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    goal = SSavingGoalCreate(
        name="mock",
        current_amount=0,
        target_amount=1000,
        target_date=date.today(),
    )
    created_goal = await saving_goals_service.set_goal(
        session=db_session,
        goal=goal,
        user_id=user.id,
    )
    assert created_goal is not None
    assert created_goal.status == GoalStatus.IN_PROGRESS

    await saving_goals_service._complete_saving_goal(
        goal_id=created_goal.id,
        session=db_session,
    )
    updated_goal = await saving_goals_service.get_goal(
        goal_id=created_goal.id,
        user_id=user.id,
        session=db_session,
    )
    assert updated_goal is not None
    assert updated_goal.status == GoalStatus.COMPLETED
