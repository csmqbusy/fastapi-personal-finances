from datetime import date, timedelta

import pytest
from factory.faker import faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel
from app.repositories.saving_goals_repository import saving_goals_repo
from app.schemas.common_schemas import SortParam
from app.schemas.saving_goals_schemas import GoalStatus
from tests.factories import SavingGoalFactory
from tests.helpers import add_obj_to_db, create_batch

fake = faker.Faker()


@pytest.mark.asyncio
@pytest.mark.parametrize("goals_qty", [1, 5, 50, 0])
async def test_get_goals_from_db__without_filters(
    db_session: AsyncSession,
    user: UserModel,
    goals_qty: int,
):
    await create_batch(
        db_session, goals_qty, SavingGoalFactory, dict(user_id=user.id)
    )
    goals = await saving_goals_repo.get_goals_from_db(db_session, user.id)
    assert len(goals) == goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "min_current_amount",
        "max_current_amount",
        "min_target_amount",
        "max_target_amount",
        "expected_goals_qty",
    ),
    [
        (0, 20000, 15000, 100000, 8),
        (1, 19999, 22001, 39999, 3),
        (500, None, None, None, 7),
        (None, 1000, None, None, 3),
        (None, None, 40000, None, 3),
        (None, None, None, 33000, 4),
        (None, None, None, None, 8),
    ],
)
async def test_get_goals_from_db__with_amounts(
    db_session: AsyncSession,
    user: UserModel,
    min_current_amount: int | None,
    max_current_amount: int | None,
    min_target_amount: int | None,
    max_target_amount: int | None,
    expected_goals_qty: int,
):
    current_amounts = [0, 500, 1000, 2000, 4000, 8000, 15000, 20000]
    target_amounts = [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000]
    for i in range(len(current_amounts)):
        obj = SavingGoalFactory(
            current_amount=current_amounts[i],
            target_amount=target_amounts[i],
            user_id=user.id,
        )
        await add_obj_to_db(obj, db_session)

    goals = await saving_goals_repo.get_goals_from_db(
        session=db_session,
        user_id=user.id,
        min_current_amount=min_current_amount,
        max_current_amount=max_current_amount,
        min_target_amount=min_target_amount,
        max_target_amount=max_target_amount,
    )
    assert len(goals) == expected_goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name_search_term, description_search_term, expected_goals_qty",
    [
        ("NAME", "DESC", 2),
        ("NA", None, 5),
        ("@", None, 1),
        (None, "desc", 3),
        (None, "3", 1),
        (None, None, 6),
    ],
)
async def test_get_goals_from_db__with_search_terms(
    db_session: AsyncSession,
    user: UserModel,
    name_search_term: str | None,
    description_search_term: str | None,
    expected_goals_qty: int,
):
    names = ["name", "n@m3", " name ", "_name_", "some name", "bad NAME"]
    descs = ["de3c", "desc ", "description", "", "some desc ", "d"]
    for i in range(len(names)):
        obj = SavingGoalFactory(
            name=names[i],
            description=descs[i],
            user_id=user.id,
        )
        await add_obj_to_db(obj, db_session)

    goals = await saving_goals_repo.get_goals_from_db(
        session=db_session,
        user_id=user.id,
        name_search_term=name_search_term,
        desc_search_term=description_search_term,
    )
    assert len(goals) == expected_goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "start_date_from",
        "start_date_to",
        "target_date_from",
        "target_date_to",
        "expected_goals_qty",
    ),
    [
        (
            date(2025, 1, 1),
            date(2025, 12, 31),
            date(2026, 1, 1),
            date(2026, 12, 31),
            8,
        ),
        (date(2025, 1, 1), None, date(2026, 1, 1), None, 8),
        (None, date(2025, 3, 20), None, date(2026, 3, 20), 3),
        (date(2025, 12, 31), date(2025, 12, 31), None, None, 1),
        (None, None, date(2026, 12, 31), date(2026, 12, 31), 1),
        (None, None, None, None, 8),
    ],
)
async def test_get_goals_from_db__with_dates_ranges(
    db_session: AsyncSession,
    user: UserModel,
    start_date_from: date | None,
    start_date_to: date | None,
    target_date_from: date | None,
    target_date_to: date | None,
    expected_goals_qty: int,
):
    start_dates = [
        date(2025, 1, 1),
        date(2025, 2, 15),
        date(2025, 3, 20),
        date(2025, 5, 23),
        date(2025, 6, 30),
        date(2025, 8, 26),
        date(2025, 10, 10),
        date(2025, 12, 31),
    ]
    target_dates = [
        date(2026, 1, 1),
        date(2026, 2, 15),
        date(2026, 3, 20),
        date(2026, 5, 23),
        date(2026, 6, 30),
        date(2026, 8, 26),
        date(2026, 10, 10),
        date(2026, 12, 31),
    ]
    for i in range(len(start_dates)):
        obj = SavingGoalFactory(
            start_date=start_dates[i],
            target_date=target_dates[i],
            user_id=user.id,
        )
        await add_obj_to_db(obj, db_session)

    goals = await saving_goals_repo.get_goals_from_db(
        session=db_session,
        user_id=user.id,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        target_date_from=target_date_from,
        target_date_to=target_date_to,
    )
    assert len(goals) == expected_goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "end_date_from, end_date_to, expected_goals_qty",
    [
        (date.today(), date.today(), 3),
        (date.today(), None, 3),
        (None, date.today(), 3),
        (date.today() + timedelta(days=1), date.today() + timedelta(days=1), 0),
        (date.today() - timedelta(days=1), date.today() - timedelta(days=1), 0),
    ],
)
async def test_get_goals_from_db__with_end_date_range(
    db_session: AsyncSession,
    user: UserModel,
    end_date_from: date | None,
    end_date_to: date | None,
    expected_goals_qty: int,
):
    goals_qty = 3
    for i in range(goals_qty):
        obj = SavingGoalFactory(
            current_amount=5000,
            target_amount=5000,
            end_date=date.today(),
            user_id=user.id,
        )
        await add_obj_to_db(obj, db_session)

    goals = await saving_goals_repo.get_goals_from_db(
        session=db_session,
        user_id=user.id,
        end_date_from=end_date_from,
        end_date_to=end_date_to,
    )
    assert len(goals) == expected_goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, expected_goals_qty",
    [
        (GoalStatus.IN_PROGRESS, 3),
        (GoalStatus.COMPLETED, 3),
        (GoalStatus.OVERDUE, 3),
        (None, 9),
    ],
)
async def test_get_goals_from_db__with_status(
    db_session: AsyncSession,
    user: UserModel,
    status: GoalStatus | None,
    expected_goals_qty: int,
):
    st = [GoalStatus.IN_PROGRESS, GoalStatus.COMPLETED, GoalStatus.OVERDUE] * 3
    for i in range(len(st)):
        obj = SavingGoalFactory(
            status=st[i],
            user_id=user.id,
        )
        await add_obj_to_db(obj, db_session)

    goals = await saving_goals_repo.get_goals_from_db(
        session=db_session,
        user_id=user.id,
        status=status,
    )
    assert len(goals) == expected_goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "min_current_amount",
        "max_current_amount",
        "min_target_amount",
        "max_target_amount",
        "name_search_term",
        "desc_search_term",
        "start_date_from",
        "start_date_to",
        "target_date_from",
        "target_date_to",
        "end_date_from",
        "end_date_to",
        "status",
        "sort_params",
        "sorted_current_amounts",
        "expected_goals_qty",
    ),
    [
        (
            0,
            20000,
            15000,
            100000,
            None,
            None,
            date(2025, 1, 1),
            date(2025, 12, 31),
            date(2026, 1, 1),
            date(2026, 12, 31),
            None,
            None,
            GoalStatus.IN_PROGRESS,
            [
                SortParam(order_by="current_amount", order_direction="desc"),
            ],
            [15000, 8000, 4000, 2000, 1000, 500, 0],
            7,
        ),
        (
            500,
            20000,
            22000,
            100000,
            "name",
            "d",
            date(2025, 3, 21),
            date(2025, 12, 30),
            date(2026, 5, 24),
            date(2026, 12, 31),
            None,
            None,
            GoalStatus.IN_PROGRESS,
            [
                SortParam(order_by="current_amount", order_direction="desc"),
            ],
            [8000, 4000],
            2,
        ),
        (
            500,
            20000,
            15000,
            100000,
            "name",
            "d",
            date(2025, 3, 21),
            date(2025, 12, 31),
            date(2026, 5, 24),
            date(2026, 12, 31),
            date.today(),
            date.today(),
            GoalStatus.COMPLETED,
            [
                SortParam(order_by="current_amount", order_direction="desc"),
            ],
            [20000],
            1,
        ),
        (
            500,
            20000,
            22000,
            100000,
            "name",
            "d",
            date(2025, 3, 21),
            date(2025, 12, 30),
            date(2026, 5, 24),
            date(2026, 12, 31),
            None,
            None,
            GoalStatus.IN_PROGRESS,
            [
                SortParam(order_by="target_date", order_direction="asc"),
            ],
            [4000, 8000],
            2,
        ),
        (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            [
                SortParam(order_by="target_date", order_direction="desc"),
            ],
            [20000, 15000, 8000, 4000, 2000, 1000, 500, 0],
            8,
        ),
    ],
)
async def test_get_goals_from_db__with_all_filters(
    db_session: AsyncSession,
    user: UserModel,
    min_current_amount: int | None,
    max_current_amount: int | None,
    min_target_amount: int | None,
    max_target_amount: int | None,
    name_search_term: str | None,
    desc_search_term: str | None,
    start_date_from: date | None,
    start_date_to: date | None,
    target_date_from: date | None,
    target_date_to: date | None,
    end_date_from: date | None,
    end_date_to: date | None,
    status: GoalStatus | None,
    sort_params: list[SortParam] | None,
    sorted_current_amounts: list[int],
    expected_goals_qty: int,
):
    current_amounts = [0, 500, 1000, 2000, 4000, 8000, 15000, 20000]
    target_amounts = [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000]
    names = [
        "name",
        "n@m3",
        " name ",
        "_name_",
        "some name",
        "bad NAME",
        "n",
        "NaMe",
    ]
    descs = [
        "de3c",
        "desc ",
        "description",
        "_desc_",
        "some desc ",
        "d",
        "",
        "my desc",
    ]
    statuses = [GoalStatus.IN_PROGRESS] * 7 + [GoalStatus.COMPLETED]
    end_dates = [None] * 7 + [date.today()]
    start_dates = [
        date(2025, 1, 1),
        date(2025, 2, 15),
        date(2025, 3, 20),
        date(2025, 5, 23),
        date(2025, 6, 30),
        date(2025, 8, 26),
        date(2025, 10, 10),
        date(2025, 12, 31),
    ]
    target_dates = [
        date(2026, 1, 1),
        date(2026, 2, 15),
        date(2026, 3, 20),
        date(2026, 5, 23),
        date(2026, 6, 30),
        date(2026, 8, 26),
        date(2026, 10, 10),
        date(2026, 12, 31),
    ]
    for i in range(len(current_amounts)):
        obj = SavingGoalFactory(
            name=names[i],
            description=descs[i],
            current_amount=current_amounts[i],
            target_amount=target_amounts[i],
            start_date=start_dates[i],
            target_date=target_dates[i],
            status=statuses[i],
            end_date=end_dates[i],
            user_id=user.id,
        )
        await add_obj_to_db(obj, db_session)

    goals = await saving_goals_repo.get_goals_from_db(
        session=db_session,
        user_id=user.id,
        min_current_amount=min_current_amount,
        max_current_amount=max_current_amount,
        min_target_amount=min_target_amount,
        max_target_amount=max_target_amount,
        name_search_term=name_search_term,
        desc_search_term=desc_search_term,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        target_date_from=target_date_from,
        target_date_to=target_date_to,
        end_date_from=end_date_from,
        end_date_to=end_date_to,
        status=status,
        sort_params=sort_params,
    )
    assert len(goals) == expected_goals_qty
    assert [g.current_amount for g in goals] == sorted_current_amounts
