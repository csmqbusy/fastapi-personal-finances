from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.schemas.saving_goals_schemas import SSavingGoalResponse
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
