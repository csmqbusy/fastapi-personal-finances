from datetime import date, timedelta
from typing import ContextManager

import pytest
from dirty_equals import IsAnyStr, IsPositiveFloat, IsPositiveInt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.saving_goals_exceptions import (
    GoalCurrentAmountInvalid,
    GoalNotFound,
)
from app.models import UserModel
from app.schemas.common_schemas import SAmountRange, SDateRange
from app.schemas.saving_goals_schemas import (
    GoalStatus,
    SGoalsSortParams,
    SSavingGoalCreate,
    SSavingGoalUpdatePartial,
)
from app.services import saving_goals_service
from tests.factories import SavingGoalFactory
from tests.helpers import add_obj_to_db


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "start_date, expected_start_date",
    [
        (date(2025, 1, 1), date(2025, 1, 1)),
        (None, date.today()),
    ],
)
async def test_set_goal__success(
    db_session: AsyncSession,
    user: UserModel,
    start_date: date,
    expected_start_date: date,
):
    goal = SSavingGoalCreate.model_validate(
        SavingGoalFactory(start_date=start_date),
    )
    created_goal = await saving_goals_service.set_goal(db_session, goal, user.id)
    assert created_goal is not None
    assert created_goal.name == IsAnyStr
    assert created_goal.description == IsAnyStr
    assert created_goal.current_amount == IsPositiveInt
    assert created_goal.target_amount == IsPositiveInt
    assert created_goal.start_date == expected_start_date
    assert created_goal.status == GoalStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_set_goal__add_completed_goal(
    db_session: AsyncSession,
    user: UserModel,
):
    amount = 20000
    goal = SSavingGoalCreate.model_validate(
        SavingGoalFactory(current_amount=amount, target_amount=amount),
    )
    created_goal = await saving_goals_service.set_goal(db_session, goal, user.id)
    assert created_goal.current_amount == created_goal.target_amount == amount
    assert created_goal.status == GoalStatus.COMPLETED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, start_date, target_date",
    [
        ("Macbook Pro", date(2026, 1, 1), date(2025, 6, 20)),
        (None, date(2020, 6, 20), date(2025, 6, 20)),
    ],
)
async def test_set_goal__error(
    db_session: AsyncSession,
    user: UserModel,
    name: str,
    start_date: date,
    target_date: date,
):
    with pytest.raises(ValidationError):
        goal = SSavingGoalCreate.model_validate(
            SavingGoalFactory(
                name=name,
                start_date=start_date,
                target_date=target_date,
                user_id=user.id,
            ),
        )
        await saving_goals_service.set_goal(db_session, goal, user.id)


@pytest.mark.asyncio
async def test_get_goal__success(db_session: AsyncSession, user: UserModel):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)
    goal_from_db = await saving_goals_service.get_goal(
        goal_id=goal.id,
        user_id=user.id,
        session=db_session,
    )
    assert goal_from_db.id == goal.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_user_id, wrong_goal_id",
    [
        (None, 99999),
        (77777, None),
    ],
)
async def test_get_goal__error(
    db_session: AsyncSession,
    user: UserModel,
    wrong_user_id: int | None,
    wrong_goal_id: int | None,
):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)
    with pytest.raises(GoalNotFound):
        await saving_goals_service.get_goal(
            goal_id=wrong_goal_id or goal.id,
            user_id=wrong_user_id or user.id,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_delete_goal__success(db_session: AsyncSession, user: UserModel):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)

    await saving_goals_service.delete_goal(goal.id, user.id, db_session)
    with pytest.raises(GoalNotFound):
        await saving_goals_service.get_goal(goal.id, user.id, db_session)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_user_id, wrong_goal_id",
    [
        (None, 99999),
        (77777, None),
    ],
)
async def test_delete_goal__error(
    db_session: AsyncSession,
    user: UserModel,
    wrong_goal_id: int | None,
    wrong_user_id: int | None,
):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)
    with pytest.raises(GoalNotFound):
        await saving_goals_service.delete_goal(
            goal_id=wrong_goal_id or goal.id,
            user_id=wrong_user_id or user.id,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_update_goal__success_full_update(
    db_session: AsyncSession,
    user: UserModel,
    saving_goal_update_obj: SSavingGoalUpdatePartial,
):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)

    assert goal.name != saving_goal_update_obj.name
    assert goal.description != saving_goal_update_obj.description
    assert goal.current_amount != saving_goal_update_obj.current_amount
    assert goal.target_amount != saving_goal_update_obj.target_amount
    assert goal.start_date != saving_goal_update_obj.start_date
    assert goal.target_date != saving_goal_update_obj.target_date

    updated_goal = await saving_goals_service.update_goal(
        goal_id=goal.id,
        user_id=user.id,
        goal_update_obj=saving_goal_update_obj,
        session=db_session,
    )
    assert updated_goal is not None
    assert updated_goal.name == saving_goal_update_obj.name
    assert updated_goal.description == saving_goal_update_obj.description
    assert updated_goal.current_amount == saving_goal_update_obj.current_amount
    assert updated_goal.target_amount == saving_goal_update_obj.target_amount
    assert updated_goal.start_date == saving_goal_update_obj.start_date
    assert updated_goal.target_date == saving_goal_update_obj.target_date


@pytest.mark.asyncio
async def test_update_goal__success_partial_update(
    db_session: AsyncSession,
    user: UserModel,
    saving_goal_update_obj: SSavingGoalUpdatePartial,
):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)
    saving_goal_update_obj.description = None
    saving_goal_update_obj.target_amount = None
    saving_goal_update_obj.start_date = None
    saving_goal_update_obj.target_date = None

    updated_goal = await saving_goals_service.update_goal(
        goal_id=goal.id,
        user_id=user.id,
        goal_update_obj=saving_goal_update_obj,
        session=db_session,
    )
    assert updated_goal is not None
    assert updated_goal.name == saving_goal_update_obj.name
    assert updated_goal.description == goal.description
    assert updated_goal.current_amount == saving_goal_update_obj.current_amount
    assert updated_goal.target_amount == goal.target_amount
    assert updated_goal.start_date == goal.start_date
    assert updated_goal.target_date == goal.target_date


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "new_current_amount, new_target_amount, new_start_date, new_target_date",
    [
        (None, None, date(2021, 1, 1), date(2020, 1, 1)),
        (200001, 200000, None, None),
    ],
)
async def test_update_goal__error(
    db_session: AsyncSession,
    user: UserModel,
    new_current_amount: int | None,
    new_target_amount: int | None,
    new_start_date: date | None,
    new_target_date: date | None,
):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)

    with pytest.raises(ValidationError):
        goal_update_obj = SSavingGoalUpdatePartial(
            current_amount=new_current_amount,
            target_amount=new_target_amount,
            start_date=new_start_date,
            target_date=new_target_date,
        )
        await saving_goals_service.update_goal(
            goal_id=goal.id,
            user_id=user.id,
            goal_update_obj=goal_update_obj,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_get_goal_progress__success(
    db_session: AsyncSession,
    user: UserModel,
):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)
    goal_progress = await saving_goals_service.get_goal_progress(
        goal_id=goal.id,
        user_id=user.id,
        session=db_session,
    )
    assert goal_progress.current_amount == goal.current_amount
    assert goal_progress.target_amount == goal.target_amount
    assert goal_progress.rest_amount == goal.target_amount - goal.current_amount
    assert goal_progress.percentage_progress == IsPositiveFloat
    assert goal_progress.days_left is not None
    assert goal_progress.expected_daily_payment == IsPositiveInt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_user_id, wrong_goal_id",
    [
        (9999, None),
        (None, 9999),
    ],
)
async def test_get_goal_progress__error(
    db_session: AsyncSession,
    user: UserModel,
    wrong_user_id: int | None,
    wrong_goal_id: int | None,
):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)
    with pytest.raises(GoalNotFound):
        await saving_goals_service.get_goal_progress(
            goal_id=wrong_goal_id or goal.id,
            user_id=wrong_user_id or user.id,
            session=db_session,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payment, expected_status, expected_current_amount",
    [
        (20000, GoalStatus.IN_PROGRESS, 20000),
        (200000, GoalStatus.COMPLETED, 200000),
    ],
)
async def test_update_current_amount__success(
    db_session: AsyncSession,
    user: UserModel,
    payment: int,
    expected_status: GoalStatus,
    expected_current_amount: int,
):
    current_amount = 0
    target_amount = 200000
    goal = SavingGoalFactory(
        user_id=user.id,
        current_amount=current_amount,
        target_amount=target_amount,
    )
    await add_obj_to_db(goal, db_session)

    updated_goal = await saving_goals_service.update_current_amount(
        goal_id=goal.id,
        user_id=user.id,
        payment=payment,
        session=db_session,
    )
    assert updated_goal.current_amount == expected_current_amount
    assert updated_goal.status == expected_status


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payment, wrong_user_id, wrong_goal_id, expectation",
    [
        (-10001, None, None, pytest.raises(GoalCurrentAmountInvalid)),
        (1000, 9999, None, pytest.raises(GoalNotFound)),
        (1000, None, 9999, pytest.raises(GoalNotFound)),
    ],
)
async def test_update_current_amount__error(
    db_session: AsyncSession,
    user: UserModel,
    payment: int,
    wrong_user_id: int | None,
    wrong_goal_id: int | None,
    expectation: ContextManager,
):
    current_amount = 10000
    target_amount = 200000
    goal = SavingGoalFactory(
        user_id=user.id,
        current_amount=current_amount,
        target_amount=target_amount,
    )
    await add_obj_to_db(goal, db_session)

    with expectation:
        await saving_goals_service.update_current_amount(
            goal_id=wrong_goal_id or goal.id,
            user_id=wrong_user_id or user.id,
            payment=payment,
            session=db_session,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "current_amount_range, target_amount_range, expected_goals_qty",
    [
        (
            SAmountRange(min_amount=0, max_amount=1500),
            SAmountRange(min_amount=5000, max_amount=15000),
            3,
        ),
        (
            SAmountRange(min_amount=None, max_amount=None),
            SAmountRange(min_amount=None, max_amount=None),
            6,
        ),
        (
            SAmountRange(min_amount=None, max_amount=2000),
            SAmountRange(min_amount=None, max_amount=20000),
            4,
        ),
        (
            SAmountRange(min_amount=500, max_amount=None),
            SAmountRange(min_amount=30000, max_amount=None),
            1,
        ),
    ],
)
async def test_get_goals_all__with_amounts_range(
    db_session: AsyncSession,
    user: UserModel,
    current_amount_range: SAmountRange,
    target_amount_range: SAmountRange,
    expected_goals_qty: int,
):
    current_amounts = [0, 500, 1000, 1500, 2000, 2500]
    target_amounts = [5000, 10000, 15000, 20000, 25000, 30000]
    for ca, ta in zip(current_amounts, target_amounts):
        goal = SavingGoalFactory(
            user_id=user.id, current_amount=ca, target_amount=ta
        )
        await add_obj_to_db(goal, db_session)

    goals = await saving_goals_service.get_goals_all(
        session=db_session,
        user_id=user.id,
        current_amount_range=current_amount_range,
        target_amount_range=target_amount_range,
    )
    current_min_amount = current_amount_range.min_amount or 0
    current_max_amount = current_amount_range.max_amount or float("inf")
    target_min_amount = target_amount_range.min_amount or 0
    target_max_amount = target_amount_range.max_amount or float("inf")

    assert len(goals) == expected_goals_qty
    for goal in goals:
        assert current_min_amount <= goal.current_amount <= current_max_amount
        assert target_min_amount <= goal.target_amount <= target_max_amount


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name_search_term, description_search_term, expected_goals_qty",
    [
        ("text", "description", 2),
        ("text", "desc", 3),
        ("T3XT", None, 1),
        (None, "desc ", 1),
    ],
)
async def test_get_goals_all__with_search_terms(
    db_session: AsyncSession,
    user: UserModel,
    name_search_term: str | None,
    description_search_term: str | None,
    expected_goals_qty: int,
):
    names = ["TEXT", "text", " text ", "t3xT   "]
    descs = [" some description", "description text", "my desc text", "desc"]
    for nm, dsc in zip(names, descs):
        goal = SavingGoalFactory(user_id=user.id, name=nm, description=dsc)
        await add_obj_to_db(goal, db_session)

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
    "start_date_range, target_date_range, expected_goals_qty",
    [
        (
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            5,
        ),
        (
            SDateRange(start=date(2025, 1, 1), end=date(2025, 3, 31)),
            SDateRange(start=date(2025, 12, 28), end=date(2025, 12, 31)),
            2,
        ),
        (
            SDateRange(start=date(2025, 5, 1), end=date(2025, 12, 31)),
            None,
            1,
        ),
        (
            None,
            SDateRange(start=date(2025, 12, 29), end=date(2025, 12, 31)),
            3,
        ),
    ],
)
async def test_get_goals_all__with_date_ranges(
    db_session: AsyncSession,
    user: UserModel,
    start_date_range: SDateRange | None,
    target_date_range: SDateRange | None,
    expected_goals_qty: int,
):
    start_dates = [
        date(2025, 1, 1),
        date(2025, 2, 1),
        date(2025, 3, 1),
        date(2025, 4, 1),
        date(2025, 5, 1),
    ]
    target_dates = [
        date(2025, 12, 27),
        date(2025, 12, 28),
        date(2025, 12, 29),
        date(2025, 12, 30),
        date(2025, 12, 31),
    ]
    for sd, td in zip(start_dates, target_dates):
        goal = SavingGoalFactory(user_id=user.id, start_date=sd, target_date=td)
        await add_obj_to_db(goal, db_session)

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
    "goals_qty, end_date_range, expected_goals_qty",
    [
        (5, SDateRange(start=date.today(), end=date.today()), 5),
        (5, SDateRange(start=date(2020, 1, 1), end=date(2023, 1, 1)), 0),
    ],
)
async def test_get_goals_all__with_end_date_range(
    db_session: AsyncSession,
    user: UserModel,
    goals_qty: int,
    end_date_range: SDateRange,
    expected_goals_qty: int,
):
    for i in range(goals_qty):
        goal = SSavingGoalCreate.model_validate(
            SavingGoalFactory(
                current_amount=1000,
                target_amount=1000,
                user_id=user.id,
            ),
        )
        await saving_goals_service.set_goal(db_session, goal, user.id)

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
    "status, expected_goals_qty",
    [
        (GoalStatus.IN_PROGRESS, 1),
        (GoalStatus.COMPLETED, 1),
        (GoalStatus.OVERDUE, 1),
    ],
)
async def test_get_goals_all__with_status(
    db_session: AsyncSession,
    user: UserModel,
    status: GoalStatus,
    expected_goals_qty: int,
):
    statuses = [GoalStatus.IN_PROGRESS, GoalStatus.COMPLETED, GoalStatus.OVERDUE]
    for s in statuses:
        goal = SavingGoalFactory(user_id=user.id, status=s)
        await add_obj_to_db(goal, db_session)

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
        "current_amount_range",
        "target_amount_range",
        "name_search_term",
        "description_search_term",
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
            SAmountRange(min_amount=0, max_amount=3000),
            SAmountRange(min_amount=5000, max_amount=20000),
            "text",
            "desc",
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            SDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31)),
            None,
            GoalStatus.IN_PROGRESS,
            SGoalsSortParams(sort_by=["-target_amount", "-current_amount"]),
            [20000, 15000, 10000, 5000],
            4,
        ),
    ],
)
async def test_get_goals_all__with_all_filters(
    db_session: AsyncSession,
    user: UserModel,
    current_amount_range: SAmountRange,
    target_amount_range: SAmountRange,
    name_search_term: str,
    description_search_term: str,
    start_date_range: SDateRange,
    target_date_range: SDateRange,
    end_date_range: SDateRange | None,
    status: GoalStatus,
    sort_params: SGoalsSortParams,
    sorted_target_amounts: list[int],
    expected_goals_qty: int,
):
    current_amounts = [0, 1000, 2000, 3000, 4000]
    target_amounts = [5000, 15000, 10000, 20000, 30000]
    names = ["TEXT", "TEXT", "text", " text ", "t3xT   "]
    descs = [" some description", "description text", "my desc ", "desc", " "]
    start_dates = [
        date(2025, 1, 1),
        date(2025, 2, 1),
        date(2025, 3, 1),
        date(2025, 4, 1),
        date(2025, 5, 1),
    ]
    target_dates = [
        date(2025, 12, 27),
        date(2025, 12, 28),
        date(2025, 12, 29),
        date(2025, 12, 30),
        date(2025, 12, 31),
    ]
    statuses = [GoalStatus.IN_PROGRESS] * 5

    for i in range(len(current_amounts)):
        goal = SavingGoalFactory(
            user_id=user.id,
            name=names[i],
            description=descs[i],
            target_amount=target_amounts[i],
            current_amount=current_amounts[i],
            target_date=target_dates[i],
            start_date=start_dates[i],
            status=statuses[i],
        )
        await add_obj_to_db(goal, db_session)

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
async def test__complete_saving_goal(db_session: AsyncSession, user: UserModel):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)
    assert goal.status == GoalStatus.IN_PROGRESS

    await saving_goals_service._complete_saving_goal(
        goal_id=goal.id,
        session=db_session,
    )
    updated_goal = await saving_goals_service.get_goal(
        goal_id=goal.id,
        user_id=user.id,
        session=db_session,
    )
    assert updated_goal.status == GoalStatus.COMPLETED


@pytest.mark.parametrize(
    "first_num, second_num, expected_result",
    [
        (1, 100, 1.0),
        (0, 100, 0.0),
        (330, 2000, 16.5),
        (331, 2000, 16.55),
        (17500, 233000, 7.51),
        (17500, 233000, 7.51),
        (3171631, 31489307, 10.07),
        (200, 200, 100.0),
    ],
)
def test_get_percentage(first_num: int, second_num: int, expected_result: float):
    percent = saving_goals_service.get_percentage(first_num, second_num)
    assert percent == expected_result


@pytest.mark.parametrize(
    "date1, date2, expected_result",
    [
        (date(2025, 1, 1), date(2025, 1, 1), 0),
        (date(2025, 1, 1), date(2025, 1, 2), 1),
        (date(2025, 1, 1), date(2025, 1, 20), 19),
        (date(2023, 12, 1), date(2025, 3, 5), 460),
        (date(2025, 3, 5), date(2023, 12, 1), 460),
    ],
)
def test_get_days_before_dates(date1: date, date2: date, expected_result: int):
    days = saving_goals_service.get_days_between_dates(d1=date1, d2=date2)
    assert days == expected_result


@pytest.mark.parametrize(
    "amount, rest_days, expected_result",
    [
        (3000, 10, 300),
        (3332300, 250, 13329),
        (2000, 1, 2000),
        (2000, 0, 2000),
        (0, 100, 0),
    ],
)
def test_get_expected_daily_payment(
    amount: int,
    rest_days: int,
    expected_result: int,
):
    daily_payment = saving_goals_service.get_expected_daily_payment(
        rest_amount=amount,
        days_left=rest_days,
    )
    assert daily_payment == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "target_date, result",
    [
        (date.today(), False),
        (date.today() + timedelta(days=1), False),
        (date.today() - timedelta(days=1), True),
    ],
)
async def test__is_goal_overdue(
    db_session: AsyncSession,
    user: UserModel,
    target_date: date,
    result: bool,
):
    goal = SavingGoalFactory(user_id=user.id, target_date=target_date)
    await add_obj_to_db(goal, db_session)

    assert saving_goals_service._is_goal_overdue(goal) is result


@pytest.mark.asyncio
async def test_make_saving_goal_overdue(
    db_session: AsyncSession,
    user: UserModel,
):
    goal = SavingGoalFactory(user_id=user.id)
    await add_obj_to_db(goal, db_session)
    assert goal.status == GoalStatus.IN_PROGRESS

    await saving_goals_service.make_saving_goal_overdue(goal.id, db_session)
    assert goal.status == GoalStatus.OVERDUE
