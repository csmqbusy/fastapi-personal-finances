from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.schemas.saving_goals_schemas import (
    SSavingGoalResponse,
    SSavingGoalProgress,
)
from tests.integration.helpers import sign_up_user, sign_in_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "name",
        "current_amount",
        "target_amount",
        "target_date",
    ),
    [
        (
            "10Henry1",
            status.HTTP_201_CREATED,
            "Macbook Pro 2025",
            0,
            250000,
            date(2025, 12, 31),
        ),
        (
            "10Henry2",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            None,
            0,
            250000,
            date(2025, 12, 31),
        ),
        (
            "10Henry3",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Macbook Pro 2025",
            -300,
            250000,
            date(2025, 12, 31),
        ),
        (
            "10Henry3",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Macbook Pro 2025",
            251000,
            250000,
            date(2025, 12, 31),
        ),
    ]
)
async def test_goals__post(
    client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    name: str,
    current_amount: int,
    target_amount: int,
    target_date: date,
):
    await sign_up_user(client, username)
    await sign_in_user(client, username)

    response = await client.post(
        url=f"{settings.api.prefix_v1}/goals/",
        json={
            "name": name,
            "current_amount": current_amount,
            "target_amount": target_amount,
            "target_date": target_date.isoformat(),
        }
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_201_CREATED:
        response_schema = SSavingGoalResponse.model_validate(response.json())
        assert type(response_schema) is SSavingGoalResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "name",
        "current_amount",
        "target_amount",
        "target_date",
        "pass_invalid_goal_id",
        "sign_in_another_user",
    ),
    [
        (
            "20Henry1",
            status.HTTP_200_OK,
            "Macbook Pro 2025",
            0,
            250000,
            date(2025, 12, 31),
            False,
            False,
        ),
        (
            "20Henry2",
            status.HTTP_404_NOT_FOUND,
            "Macbook Pro 2025",
            0,
            250000,
            date(2025, 12, 31),
            True,
            False,
        ),
        (
            "20Henry2",
            status.HTTP_404_NOT_FOUND,
            "Macbook Pro 2025",
            0,
            250000,
            date(2025, 12, 31),
            False,
            True,
        ),
    ]
)
async def test_saving_goal_progress_get(
    client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    name: str,
    current_amount: int,
    target_amount: int,
    target_date: date,
    pass_invalid_goal_id: bool,
    sign_in_another_user: bool,
):
    await sign_up_user(client, username)
    await sign_in_user(client, username)

    response = await client.post(
        url=f"{settings.api.prefix_v1}/goals/",
        json={
            "name": name,
            "current_amount": current_amount,
            "target_amount": target_amount,
            "target_date": target_date.isoformat(),
        }
    )
    goal_id = 99999 if pass_invalid_goal_id else response.json()["id"]

    if sign_in_another_user:
        another_username = f"Another{username}"
        await sign_up_user(client, another_username)
        await sign_in_user(client, another_username)

    response = await client.get(
        url=f"{settings.api.prefix_v1}/goals/progress/{goal_id}/",
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_schema = SSavingGoalProgress.model_validate(response.json())
        assert type(response_schema) is SSavingGoalProgress
