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

