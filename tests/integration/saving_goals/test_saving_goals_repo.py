from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_repo
from app.repositories.saving_goals_repository import saving_goals_repo
from app.schemas.saving_goals_schemas import SSavingGoalCreate
from app.services import saving_goals_service
from tests.integration.helpers import add_mock_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, goals_qty",
    [
        (
            "10Ronaldo1",
            5,
        ),
        (
            "10Ronaldo2",
            50,
        ),
        (
            "10Ronaldo3",
            0,
        ),
    ]
)
async def test_get_goals_from_db__without_filters(
    db_session: AsyncSession,
    username: str,
    goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for _ in range(goals_qty):
        goal = SSavingGoalCreate(
            name="name",
            current_amount=0,
            target_amount=5000,
            target_date=date.today(),
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

    goals = await saving_goals_repo.get_goals_from_db(
        session=db_session,
        user_id=user.id,
    )
    assert len(goals) == goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "current_amounts",
        "target_amounts",
        "min_current_amount",
        "max_current_amount",
        "min_target_amount",
        "max_target_amount",
        "expected_goals_qty",
    ),
    [
        (
            "20Ronaldo1",
            [0, 500, 1000, 2000, 4000, 8000, 15000, 20000],
            [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000],
            0,
            50000,
            0,
            5000000,
            8,
        ),
        (
            "20Ronaldo2",
            [0, 500, 1000, 2000, 4000, 8000, 15000, 20000],
            [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000],
            0,
            20000,
            0,
            100000,
            8,
        ),
        (
            "20Ronaldo3",
            [0, 500, 1000, 2000, 4000, 8000, 15000, 20000],
            [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000],
            None,
            None,
            None,
            None,
            8,
        ),
        (
            "20Ronaldo4",
            [0, 500, 1000, 2000, 4000, 8000, 15000, 20000],
            [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000],
            500,
            None,
            None,
            None,
            7,
        ),
        (
            "20Ronaldo5",
            [0, 500, 1000, 2000, 4000, 8000, 15000, 20000],
            [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000],
            None,
            1000,
            None,
            None,
            3,
        ),
        (
            "20Ronaldo6",
            [0, 500, 1000, 2000, 4000, 8000, 15000, 20000],
            [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000],
            None,
            None,
            40000,
            None,
            3,
        ),
        (
            "20Ronaldo7",
            [0, 500, 1000, 2000, 4000, 8000, 15000, 20000],
            [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000],
            None,
            None,
            None,
            33000,
            4,
        ),
        (
            "20Ronaldo8",
            [0, 500, 1000, 2000, 4000, 8000, 15000, 20000],
            [15000, 22000, 25000, 33000, 35000, 40000, 40000, 100000],
            1,
            19999,
            22001,
            39999,
            3,
        ),
    ]
)
async def test_get_goals_from_db__with_amounts(
    db_session: AsyncSession,
    username: str,
    current_amounts: list[int],
    target_amounts: list[int],
    min_current_amount: int | None,
    max_current_amount: int | None,
    min_target_amount: int | None,
    max_target_amount: int | None,
    expected_goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for i in range(len(current_amounts)):
        goal = SSavingGoalCreate(
            name="name",
            current_amount=current_amounts[i],
            target_amount=target_amounts[i],
            target_date=date.today(),
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

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
            "30Ronaldo1",
            ["name", "n@m3", " name ", "_name_", "some name", "bad NAME", "n", "NaMe"],
            ["de3c", "desc ", "description", "_desc_", "some desc ", "d", "", "my desc"],
            "NAME",
            "DESC",
            4,
        ),
        (
            "30Ronaldo2",
            ["name", "n@m3", " name ", "_name_", "some name", "bad NAME", "n", "NaMe"],
            ["de3c", "desc ", "description", "_desc_", "some desc ", "d", "", "my desc"],
            None,
            None,
            8,
        ),
        (
            "30Ronaldo3",
            ["name", "n@m3", " name ", "_name_", "some name", "bad NAME", "n", "NaMe"],
            ["de3c", "desc ", "description", "_desc_", "some desc ", "d", "", "my desc"],
            "NA",
            None,
            6,
        ),
        (
            "30Ronaldo4",
            ["name", "n@m3", " name ", "_name_", "some name", "bad NAME", "n", "NaMe"],
            ["de3c", "desc ", "description", "_desc_", "some desc ", "d", "", "my desc"],
            "@",
            None,
            1,
        ),
        (
            "30Ronaldo5",
            ["name", "n@m3", " name ", "_name_", "some name", "bad NAME", "n", "NaMe"],
            ["de3c", "desc ", "description", "_desc_", "some desc ", "d", "", "my desc"],
            None,
            "3",
            1,
        ),
        (
            "30Ronaldo6",
            ["name", "n@m3", " name ", "_name_", "some name", "bad NAME", "n", "NaMe"],
            ["de3c", "desc ", "description", "_desc_", "some desc ", "d", "", "my desc"],
            None,
            "description",
            1,
        ),
        (
            "30Ronaldo7",
            ["name", "n@m3", " name ", "_name_", "some name", "bad NAME", "n", "NaMe"],
            ["de3c", "desc ", "description", "_desc_", "some desc ", "d", "", "my desc"],
            None,
            "desc",
            5,
        ),
    ]
)
async def test_get_goals_from_db__with_search_terms(
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
            target_amount=5000,
            target_date=date.today(),
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

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
        "username",
        "start_dates",
        "target_dates",
        "start_date_from",
        "start_date_to",
        "target_date_from",
        "target_date_to",
        "expected_goals_qty",
    ),
    [
        (
            "40Ronaldo1",
            [
                date(2025, 1, 1),
                date(2025, 2, 15),
                date(2025, 3, 20),
                date(2025, 5, 23),
                date(2025, 6, 30),
                date(2025, 8, 26),
                date(2025, 10, 10),
                date(2025, 12, 31),
            ],
            [
                date(2026, 1, 1),
                date(2026, 2, 15),
                date(2026, 3, 20),
                date(2026, 5, 23),
                date(2026, 6, 30),
                date(2026, 8, 26),
                date(2026, 10, 10),
                date(2026, 12, 31),
            ],
            date(2025, 1, 1),
            date(2025, 12, 31),
            date(2026, 1, 1),
            date(2026, 12, 31),
            8,
        ),
        (
            "40Ronaldo2",
            [
                date(2025, 1, 1),
                date(2025, 2, 15),
                date(2025, 3, 20),
                date(2025, 5, 23),
                date(2025, 6, 30),
                date(2025, 8, 26),
                date(2025, 10, 10),
                date(2025, 12, 31),
            ],
            [
                date(2026, 1, 1),
                date(2026, 2, 15),
                date(2026, 3, 20),
                date(2026, 5, 23),
                date(2026, 6, 30),
                date(2026, 8, 26),
                date(2026, 10, 10),
                date(2026, 12, 31),
            ],
            date(2025, 1, 1),
            None,
            date(2026, 1, 1),
            None,
            8,
        ),
        (
            "40Ronaldo3",
            [
                date(2025, 1, 1),
                date(2025, 2, 15),
                date(2025, 3, 20),
                date(2025, 5, 23),
                date(2025, 6, 30),
                date(2025, 8, 26),
                date(2025, 10, 10),
                date(2025, 12, 31),
            ],
            [
                date(2026, 1, 1),
                date(2026, 2, 15),
                date(2026, 3, 20),
                date(2026, 5, 23),
                date(2026, 6, 30),
                date(2026, 8, 26),
                date(2026, 10, 10),
                date(2026, 12, 31),
            ],
            None,
            None,
            None,
            None,
            8,
        ),
        (
            "40Ronaldo4",
            [
                date(2025, 1, 1),
                date(2025, 2, 15),
                date(2025, 3, 20),
                date(2025, 5, 23),
                date(2025, 6, 30),
                date(2025, 8, 26),
                date(2025, 10, 10),
                date(2025, 12, 31),
            ],
            [
                date(2026, 1, 1),
                date(2026, 2, 15),
                date(2026, 3, 20),
                date(2026, 5, 23),
                date(2026, 6, 30),
                date(2026, 8, 26),
                date(2026, 10, 10),
                date(2026, 12, 31),
            ],
            None,
            date(2025, 3, 20),
            None,
            date(2026, 3, 20),
            3,
        ),
        (
            "40Ronaldo5",
            [
                date(2025, 1, 1),
                date(2025, 2, 15),
                date(2025, 3, 20),
                date(2025, 5, 23),
                date(2025, 6, 30),
                date(2025, 8, 26),
                date(2025, 10, 10),
                date(2025, 12, 31),
            ],
            [
                date(2026, 1, 1),
                date(2026, 2, 15),
                date(2026, 3, 20),
                date(2026, 5, 23),
                date(2026, 6, 30),
                date(2026, 8, 26),
                date(2026, 10, 10),
                date(2026, 12, 31),
            ],
            date(2025, 12, 31),
            date(2025, 12, 31),
            None,
            None,
            1,
        ),
        (
            "40Ronaldo6",
            [
                date(2025, 1, 1),
                date(2025, 2, 15),
                date(2025, 3, 20),
                date(2025, 5, 23),
                date(2025, 6, 30),
                date(2025, 8, 26),
                date(2025, 10, 10),
                date(2025, 12, 31),
            ],
            [
                date(2026, 1, 1),
                date(2026, 2, 15),
                date(2026, 3, 20),
                date(2026, 5, 23),
                date(2026, 6, 30),
                date(2026, 8, 26),
                date(2026, 10, 10),
                date(2026, 12, 31),
            ],
            None,
            None,
            date(2026, 12, 31),
            date(2026, 12, 31),
            1,
        ),
    ]
)
async def test_get_goals_from_db__with_dates_ranges(
    db_session: AsyncSession,
    username: str,
    start_dates: list[date],
    target_dates: list[date],
    start_date_from: date | None,
    start_date_to: date | None,
    target_date_from: date | None,
    target_date_to: date | None,
    expected_goals_qty: int,
):
    await add_mock_user(db_session, username)
    user = await user_repo.get_by_username(db_session, username)

    for i in range(len(start_dates)):
        goal = SSavingGoalCreate(
            name="names",
            current_amount=0,
            target_amount=5000,
            start_date=start_dates[i],
            target_date=target_dates[i],
        )
        await saving_goals_service.set_goal(
            session=db_session,
            goal=goal,
            user_id=user.id,
        )

    goals = await saving_goals_repo.get_goals_from_db(
        session=db_session,
        user_id=user.id,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        target_date_from=target_date_from,
        target_date_to=target_date_to,
    )
    assert len(goals) == expected_goals_qty
