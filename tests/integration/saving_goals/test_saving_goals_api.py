from datetime import date, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.models import UserModel
from app.schemas.saving_goals_schemas import (
    GoalStatus,
    SSavingGoalProgress,
    SSavingGoalResponse,
)
from tests.factories import SavingGoalFactory
from tests.helpers import (
    add_obj_to_db,
    auth_another_user,
    create_batch,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, request_params",
    [
        (
            status.HTTP_201_CREATED,
            {
                "name": "Macbook Pro 2025",
                "current_amount": 0,
                "target_amount": 250000,
            },
        ),
        (
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {
                "current_amount": 0,
                "target_amount": 250000,
            },
        ),
        (
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {
                "name": "Macbook Pro 2025",
                "current_amount": -300,
                "target_amount": 250000,
            },
        ),
        (
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {
                "name": "Macbook Pro 2025",
                "current_amount": 251000,
                "target_amount": 250000,
            },
        ),
    ],
)
async def test_goals__post(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    status_code: int,
    request_params: dict[str, Any],
):
    request_params.update({"target_date": date(2030, 1, 1).isoformat()})
    response = await client.post(
        url=f"{settings.api.prefix_v1}/goals/",
        json=request_params,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_201_CREATED:
        response_schema = SSavingGoalResponse.model_validate(response.json())
        assert type(response_schema) is SSavingGoalResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, wrong_goal_id, sign_in_another_user",
    [
        (status.HTTP_200_OK, None, False),
        (status.HTTP_404_NOT_FOUND, 99999, False),
        (status.HTTP_404_NOT_FOUND, None, True),
    ],
)
async def test_goals_progress_goal_id__get(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    status_code: int,
    wrong_goal_id: int | None,
    sign_in_another_user: bool,
):
    goal = SavingGoalFactory(user_id=auth_user.id)
    await add_obj_to_db(goal, db_session)
    goal_id = wrong_goal_id or goal.id

    if sign_in_another_user:
        await auth_another_user(db_session, client)

    response = await client.get(
        url=f"{settings.api.prefix_v1}/goals/progress/{goal_id}/",
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_schema = SSavingGoalProgress.model_validate(response.json())
        assert type(response_schema) is SSavingGoalProgress


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, wrong_goal_id, sign_in_another_user",
    [
        (status.HTTP_200_OK, None, False),
        (status.HTTP_404_NOT_FOUND, 99999, False),
        (status.HTTP_404_NOT_FOUND, None, True),
    ],
)
async def test_goals_goal_id__get(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    status_code: int,
    wrong_goal_id: int | None,
    sign_in_another_user: bool,
):
    goal = SavingGoalFactory(user_id=auth_user.id)
    await add_obj_to_db(goal, db_session)
    goal_id = wrong_goal_id or goal.id

    if sign_in_another_user:
        await auth_another_user(db_session, client)

    response = await client.get(f"{settings.api.prefix_v1}/goals/{goal_id}/")
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_schema = SSavingGoalResponse.model_validate(response.json())
        assert type(response_schema) is SSavingGoalResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, wrong_goal_id, sign_in_another_user",
    [
        (status.HTTP_200_OK, None, False),
        (status.HTTP_404_NOT_FOUND, 99999, False),
        (status.HTTP_404_NOT_FOUND, None, True),
    ],
)
async def test_goals_goal_id__delete(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    status_code: int,
    wrong_goal_id: int | None,
    sign_in_another_user: bool,
):
    goal = SavingGoalFactory(user_id=auth_user.id)
    await add_obj_to_db(goal, db_session)
    goal_id = wrong_goal_id or goal.id

    if sign_in_another_user:
        await auth_another_user(db_session, client)

    response = await client.delete(f"{settings.api.prefix_v1}/goals/{goal_id}/")
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json()["id"] == goal_id

        response = await client.get(f"{settings.api.prefix_v1}/goals/{goal_id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, payment, wrong_goal_id, sign_in_another_user",
    [
        (status.HTTP_200_OK, 200, False, False),
        (status.HTTP_400_BAD_REQUEST, -101, False, False),
        (status.HTTP_404_NOT_FOUND, 200, 99999, False),
        (status.HTTP_404_NOT_FOUND, 200, False, True),
    ],
)
async def test_goals_update_amount__patch(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    status_code: int,
    payment: int,
    wrong_goal_id: int | bool,
    sign_in_another_user: bool,
):
    goal = SavingGoalFactory(user_id=auth_user.id)
    await add_obj_to_db(goal, db_session)
    goal_id = wrong_goal_id or goal.id

    if sign_in_another_user:
        await auth_another_user(db_session, client)

    response = await client.patch(
        url=f"{settings.api.prefix_v1}/goals/update_amount/{goal_id}/",
        params={
            "payment": payment,
        },
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json()["id"] == goal_id
        assert response.json()["current_amount"] == goal.current_amount + payment


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, request_params",
    [
        (
            status.HTTP_200_OK,
            {
                "name": "new",
                "description": "new description",
                "current_amount": 2000,
                "target_amount": 100000,
                "start_date": date(2028, 1, 1).isoformat(),
                "target_date": date(2030, 1, 1).isoformat(),
            },
        ),
        (
            status.HTTP_200_OK,
            {
                "description": "new description",
                "current_amount": 2000,
                "start_date": date(2028, 1, 1).isoformat(),
            },
        ),
        (
            status.HTTP_200_OK,
            {},
        ),
    ],
)
async def test_goals_goal_id__patch__success(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    status_code: int,
    request_params: dict[str, Any],
):
    goal = SavingGoalFactory(user_id=auth_user.id)
    await add_obj_to_db(goal, db_session)

    response = await client.patch(
        url=f"{settings.api.prefix_v1}/goals/{goal.id}/",
        json=request_params,
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert request_params.items() <= response.json().items()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_goal_id, sign_in_another_user",
    [
        (99999, False),
        (None, True),
    ],
)
async def test_goals_goal_id__patch__error(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    wrong_goal_id: int | bool,
    sign_in_another_user: bool,
):
    goal = SavingGoalFactory(user_id=auth_user.id)
    await add_obj_to_db(goal, db_session)
    goal_id = wrong_goal_id or goal.id

    if sign_in_another_user:
        await auth_another_user(db_session, client)

    response = await client.patch(
        url=f"{settings.api.prefix_v1}/goals/{goal_id}/",
        json={},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_params, expected_goals_qty",
    [
        (
            {
                "min_current_amount": 0,
                "max_current_amount": 4000,
                "min_target_amount": 100000,
                "max_target_amount": 100000,
                "name_search_term": "name",
                "start_date_from": date(2028, 1, 1).isoformat(),
                "start_date_to": date(2029, 1, 1).isoformat(),
                "target_date_from": date(2030, 1, 1).isoformat(),
                "target_date_to": date(2031, 1, 1).isoformat(),
                "goal_status": GoalStatus.IN_PROGRESS,
                "page": 1,
                "page_size": 20,
                "sort_params": ["current_amount"],
            },
            5,
        ),
        (
            {
                "min_current_amount": 0,
                "max_current_amount": 4000,
                "min_target_amount": 100000,
                "max_target_amount": 100000,
                "name_search_term": "name",
                "start_date_from": date(2028, 1, 1).isoformat(),
                "start_date_to": date(2029, 1, 1).isoformat(),
                "target_date_from": date(2030, 1, 1).isoformat(),
                "target_date_to": date(2031, 1, 1).isoformat(),
                "end_date_from": date(2028, 1, 1).isoformat(),
                "end_date_to": date(2030, 1, 1).isoformat(),
                "goal_status": GoalStatus.IN_PROGRESS,
                "page": 1,
                "page_size": 1,
                "sort_params": ["current_amount"],
            },
            0,
        ),
        (
            {},
            5,
        ),
    ],
)
async def test_goals__get(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    request_params: dict[str, Any],
    expected_goals_qty: int,
):
    goals_qty = 5
    name = "name"
    description = "description"
    start_amount = 0
    amount_step = 1000
    target_amount = 100000
    start_date = date(2028, 1, 1)
    target_date = date(2030, 1, 1)
    for i in range(goals_qty):
        await client.post(
            url=f"{settings.api.prefix_v1}/goals/",
            json={
                "name": f"{name}_{i}",
                "description": f"{description}_{i}",
                "current_amount": start_amount + i * amount_step,
                "target_amount": target_amount,
                "start_date": (start_date + timedelta(days=i * 30)).isoformat(),
                "target_date": (target_date + timedelta(days=i * 30)).isoformat(),
            },
        )

    response = await client.get(
        url=f"{settings.api.prefix_v1}/goals/",
        params=request_params,
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == expected_goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "goals_qty",
    [5, 0],
)
async def test_goals__get_csv(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_user: UserModel,
    goals_qty: int,
):
    await create_batch(
        db_session, goals_qty, SavingGoalFactory, dict(user_id=auth_user.id)
    )

    response = await client.get(
        url=f"{settings.api.prefix_v1}/goals/",
        params={
            "in_csv": True,
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert type(response.content) is bytes
    assert "text/csv" in response.headers["content-type"]
    if goals_qty:
        assert len(response.content) > 2
        assert int(response.headers["content-length"]) > 1
