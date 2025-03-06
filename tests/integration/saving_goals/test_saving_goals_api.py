from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.schemas.saving_goals_schemas import (
    SSavingGoalResponse,
    SSavingGoalProgress, GoalStatus,
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
async def test_goals_progress_goal_id__get(
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "pass_invalid_goal_id",
        "sign_in_another_user",
    ),
    [
        (
            "30Henry1",
            status.HTTP_200_OK,
            False,
            False,
        ),
        (
            "30Henry2",
            status.HTTP_404_NOT_FOUND,
            True,
            False,
        ),
        (
            "30Henry3",
            status.HTTP_404_NOT_FOUND,
            False,
            True,
        ),
    ]
)
async def test_goals_goal_id__get(
    client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    pass_invalid_goal_id: bool,
    sign_in_another_user: bool,
):
    await sign_up_user(client, username)
    await sign_in_user(client, username)

    response = await client.post(
        url=f"{settings.api.prefix_v1}/goals/",
        json={
            "name": "name",
            "current_amount": 0,
            "target_amount": 1,
            "target_date": date.today().isoformat(),
        }
    )
    goal_id = 99999 if pass_invalid_goal_id else response.json()["id"]

    if sign_in_another_user:
        another_username = f"Another{username}"
        await sign_up_user(client, another_username)
        await sign_in_user(client, another_username)

    response = await client.get(
        url=f"{settings.api.prefix_v1}/goals/{goal_id}/",
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        response_schema = SSavingGoalResponse.model_validate(response.json())
        assert type(response_schema) is SSavingGoalResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "pass_invalid_goal_id",
        "sign_in_another_user",
    ),
    [
        (
            "40Henry1",
            status.HTTP_200_OK,
            False,
            False,
        ),
        (
            "40Henry2",
            status.HTTP_404_NOT_FOUND,
            True,
            False,
        ),
        (
            "40Henry3",
            status.HTTP_404_NOT_FOUND,
            False,
            True,
        ),
    ]
)
async def test_goals_goal_id__delete(
    client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    pass_invalid_goal_id: bool,
    sign_in_another_user: bool,
):
    await sign_up_user(client, username)
    await sign_in_user(client, username)

    response = await client.post(
        url=f"{settings.api.prefix_v1}/goals/",
        json={
            "name": "name",
            "current_amount": 0,
            "target_amount": 1,
            "target_date": date.today().isoformat(),
        }
    )
    goal_id = 99999 if pass_invalid_goal_id else response.json()["id"]

    if sign_in_another_user:
        another_username = f"Another{username}"
        await sign_up_user(client, another_username)
        await sign_in_user(client, another_username)

    response = await client.delete(
        url=f"{settings.api.prefix_v1}/goals/{goal_id}/",
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json()["id"] == goal_id

        response = await client.get(
            url=f"{settings.api.prefix_v1}/goals/{goal_id}/",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "current_amount",
        "target_amount",
        "payment",
        "pass_invalid_goal_id",
        "sign_in_another_user",
    ),
    [
        (
            "50Henry1",
            status.HTTP_200_OK,
            0,
            1000,
            200,
            False,
            False,
        ),
        (
            "50Henry2",
            status.HTTP_400_BAD_REQUEST,
            100,
            1000,
            -101,
            False,
            False,
        ),
        (
            "50Henry3",
            status.HTTP_404_NOT_FOUND,
            0,
            1000,
            200,
            True,
            False,
        ),
        (
            "50Henry4",
            status.HTTP_404_NOT_FOUND,
            0,
            1000,
            200,
            False,
            True,
        ),
    ]
)
async def test_goals_update_amount__patch(
    client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    current_amount: int,
    target_amount: int,
    payment: int,
    pass_invalid_goal_id: bool,
    sign_in_another_user: bool,
):
    await sign_up_user(client, username)
    await sign_in_user(client, username)

    response = await client.post(
        url=f"{settings.api.prefix_v1}/goals/",
        json={
            "name": "name",
            "current_amount": current_amount,
            "target_amount": target_amount,
            "target_date": date.today().isoformat(),
        }
    )
    goal_id = 99999 if pass_invalid_goal_id else response.json()["id"]

    if sign_in_another_user:
        another_username = f"Another{username}"
        await sign_up_user(client, another_username)
        await sign_in_user(client, another_username)

    response = await client.patch(
        url=f"{settings.api.prefix_v1}/goals/update_amount/{goal_id}/",
        params={
            "payment": payment,
        }
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json()["id"] == goal_id
        assert response.json()["current_amount"] == current_amount + payment


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "new_name",
        "new_description",
        "new_current_amount",
        "new_target_amount",
        "new_start_date",
        "new_target_date",
        "pass_invalid_goal_id",
        "sign_in_another_user",
    ),
    [
        (
            "60Henry1",
            status.HTTP_200_OK,
            "new",
            "new description",
            2000,
            100000,
            date(2028, 1, 1).isoformat(),
            date(2030, 1, 1).isoformat(),
            False,
            False,
        ),
        (
            "60Henry2",
            status.HTTP_200_OK,
            None,
            "new description",
            2000,
            None,
            date(2028, 1, 1).isoformat(),
            None,
            False,
            False,
        ),
        (
            "60Henry3",
            status.HTTP_200_OK,
            None,
            None,
            None,
            None,
            None,
            None,
            False,
            False,
        ),
        (
            "60Henry4",
            status.HTTP_404_NOT_FOUND,
            "new",
            "new description",
            2000,
            100000,
            date(2028, 1, 1).isoformat(),
            date(2030, 1, 1).isoformat(),
            True,
            False,
        ),
        (
            "60Henry5",
            status.HTTP_404_NOT_FOUND,
            "new",
            "new description",
            2000,
            100000,
            date(2028, 1, 1).isoformat(),
            date(2030, 1, 1).isoformat(),
            False,
            True,
        ),
    ]
)
async def test_goals_goal_id__patch(
    client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    new_name: str | None,
    new_description: str | None,
    new_current_amount: int | None,
    new_target_amount: int | None,
    new_start_date: str | None,
    new_target_date: str | None,
    pass_invalid_goal_id: bool,
    sign_in_another_user: bool,
):
    await sign_up_user(client, username)
    await sign_in_user(client, username)

    response = await client.post(
        url=f"{settings.api.prefix_v1}/goals/",
        json={
            "name": "name",
            "current_amount": 0,
            "target_amount": 10000,
            "target_date": date.today().isoformat(),
        }
    )
    goal_id = 99999 if pass_invalid_goal_id else response.json()["id"]

    if sign_in_another_user:
        another_username = f"Another{username}"
        await sign_up_user(client, another_username)
        await sign_in_user(client, another_username)

    response = await client.patch(
        url=f"{settings.api.prefix_v1}/goals/{goal_id}/",
        json={
            "name": new_name,
            "description": new_description,
            "current_amount": new_current_amount,
            "target_amount": new_target_amount,
            "start_date": new_start_date,
            "target_date": new_target_date,
        }
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json()["id"] == goal_id
        if new_name:
            assert response.json()["name"] == new_name
        if new_description:
            assert response.json()["description"] == new_description
        if new_current_amount:
            assert response.json()["current_amount"] == new_current_amount
        if new_target_amount:
            assert response.json()["target_amount"] == new_target_amount
        if new_start_date:
            assert response.json()["start_date"] == new_start_date
        if new_target_date:
            assert response.json()["target_date"] == new_target_date


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "goals_qty",
        "name",
        "description",
        "current_amount",
        "amount_step",
        "target_amount",
        "start_date",
        "target_date",
        "min_current_amount",
        "max_current_amount",
        "min_target_amount",
        "max_target_amount",
        "name_search_term",
        "description_search_term",
        "start_date_from",
        "start_date_to",
        "target_date_from",
        "target_date_to",
        "end_date_from",
        "end_date_to",
        "goal_status",
        "page",
        "page_size",
        "sort_params",
        "expected_goals_qty",
        "sign_in_another_user",
    ),
    [
        (
            "70Henry1",
            status.HTTP_200_OK,
            5,
            "name",
            "description",
            0,
            1000,
            100000,
            date(2028, 1, 1),
            date(2030, 1, 1),
            0,
            4000,
            100000,
            100000,
            "name",
            None,
            date(2028, 1, 1).isoformat(),
            date(2029, 1, 1).isoformat(),
            date(2030, 1, 1).isoformat(),
            date(2031, 1, 1).isoformat(),
            None,
            None,
            GoalStatus.IN_PROGRESS,
            1,
            20,
            ["current_amount"],
            5,
            False,
        ),
        (
            "70Henry2",
            status.HTTP_200_OK,
            5,
            "name",
            "description",
            0,
            1000,
            100000,
            date(2028, 1, 1),
            date(2030, 1, 1),
            0,
            4000,
            100000,
            100000,
            "name",
            None,
            date(2028, 1, 1).isoformat(),
            date(2029, 1, 1).isoformat(),
            date(2030, 1, 1).isoformat(),
            date(2031, 1, 1).isoformat(),
            None,
            None,
            GoalStatus.IN_PROGRESS,
            1,
            1,
            ["current_amount"],
            1,
            False,
        ),
        (
            "70Henry3",
            status.HTTP_200_OK,
            5,
            "name",
            "description",
            0,
            1000,
            100000,
            date(2028, 1, 1),
            date(2030, 1, 1),
            0,
            4000,
            100000,
            100000,
            "name",
            None,
            date(2028, 1, 1).isoformat(),
            date(2029, 1, 1).isoformat(),
            date(2030, 1, 1).isoformat(),
            date(2031, 1, 1).isoformat(),
            date(2028, 1, 1).isoformat(),
            date(2030, 1, 1).isoformat(),
            GoalStatus.IN_PROGRESS,
            1,
            1,
            ["current_amount"],
            0,
            False,
        ),
        (
            "70Henry4",
            status.HTTP_200_OK,
            5,
            "name",
            "description",
            0,
            1000,
            100000,
            date(2028, 1, 1),
            date(2030, 1, 1),
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
            None,
            None,
            None,
            5,
            False,
        ),
        (
            "70Henry5",
            status.HTTP_200_OK,
            5,
            "name",
            "description",
            0,
            1000,
            100000,
            date(2028, 1, 1),
            date(2030, 1, 1),
            0,
            4000,
            100000,
            100000,
            "name",
            None,
            date(2010, 1, 1).isoformat(),
            date(2050, 1, 1).isoformat(),
            date(2010, 1, 1).isoformat(),
            date(2050, 1, 1).isoformat(),
            None,
            None,
            GoalStatus.IN_PROGRESS,
            1,
            20,
            ["current_amount"],
            0,
            True,
        ),
    ]
)
async def test_goals__get(
    client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    goals_qty: int,
    name: str,
    description: str | None,
    current_amount: int,
    amount_step: int,
    target_amount: int,
    start_date: date | None,
    target_date: date,
    min_current_amount: int | None,
    max_current_amount: int | None,
    min_target_amount: int | None,
    max_target_amount: int | None,
    name_search_term: str | None,
    description_search_term: str | None,
    start_date_from: str | None,
    start_date_to: str | None,
    target_date_from: str | None,
    target_date_to: str | None,
    end_date_from: str | None,
    end_date_to: str | None,
    goal_status: GoalStatus | None,
    page: int | None,
    page_size: int | None,
    sort_params: list[str] | None,
    expected_goals_qty: int,
    sign_in_another_user: bool,
):
    await sign_up_user(client, username)
    await sign_in_user(client, username)

    for i in range(goals_qty):
        await client.post(
            url=f"{settings.api.prefix_v1}/goals/",
            json={
                "name": f"{name}_{i}",
                "description": f"{description}_{i}",
                "current_amount": current_amount + i * amount_step,
                "target_amount": target_amount,
                "start_date": (start_date + timedelta(days=i * 30)).isoformat(),
                "target_date": (target_date + timedelta(days=i * 30)).isoformat(),
            }
        )

    if sign_in_another_user:
        another_username = f"Another{username}"
        await sign_up_user(client, another_username)
        await sign_in_user(client, another_username)

    request_params = {}
    if name_search_term:
        request_params["name_search_term"] = name_search_term
    if description_search_term:
        request_params["description_search_term"] = description_search_term
    if min_current_amount:
        request_params["min_current_amount"] = min_current_amount
    if max_current_amount:
        request_params["max_current_amount"] = max_current_amount
    if min_target_amount:
        request_params["min_target_amount"] = min_target_amount
    if max_target_amount:
        request_params["max_target_amount"] = max_target_amount
    if end_date_from:
        request_params["end_date_from"] = end_date_from
    if end_date_to:
        request_params["end_date_to"] = end_date_to
    if start_date_from:
        request_params["start_date_from"] = start_date_from
    if start_date_to:
        request_params["start_date_to"] = start_date_to
    if target_date_from:
        request_params["target_date_from"] = target_date_from
    if target_date_to:
        request_params["target_date_to"] = target_date_to
    if goal_status:
        request_params["goal_status"] = goal_status
    if page:
        request_params["page"] = page
    if page_size:
        request_params["page_size"] = page_size
    if sort_params:
        request_params["sort_params"] = sort_params

    response = await client.get(
        url=f"{settings.api.prefix_v1}/goals/",
        params=request_params,
    )
    assert response.status_code == status_code
    assert len(response.json()) == expected_goals_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "goals_qty",
        "name",
        "description",
        "current_amount",
        "amount_step",
        "target_amount",
        "start_date",
        "target_date",
        "sign_in_another_user",
    ),
    [
        (
            "80Henry1",
            status.HTTP_200_OK,
            5,
            "name",
            "description",
            0,
            1000,
            100000,
            date(2028, 1, 1),
            date(2030, 1, 1),
            False,
        ),
        (
            "80Henry2",
            status.HTTP_200_OK,
            0,
            "name",
            "description",
            0,
            1000,
            100000,
            date(2028, 1, 1),
            date(2030, 1, 1),
            False,
        ),
    ]
)
async def test_goals__get_csv(
    client: AsyncClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    goals_qty: int,
    name: str,
    description: str | None,
    current_amount: int,
    amount_step: int,
    target_amount: int,
    start_date: date | None,
    target_date: date,
    sign_in_another_user: bool,
):
    await sign_up_user(client, username)
    await sign_in_user(client, username)

    for i in range(goals_qty):
        await client.post(
            url=f"{settings.api.prefix_v1}/goals/",
            json={
                "name": f"{name}_{i}",
                "description": f"{description}_{i}",
                "current_amount": current_amount + i * amount_step,
                "target_amount": target_amount,
                "start_date": (start_date + timedelta(days=i * 30)).isoformat(),
                "target_date": (target_date + timedelta(days=i * 30)).isoformat(),
            }
        )

    if sign_in_another_user:
        another_username = f"Another{username}"
        await sign_up_user(client, another_username)
        await sign_in_user(client, another_username)

    response = await client.get(
        url=f"{settings.api.prefix_v1}/goals/",
        params={
            "in_csv": True,
        }
    )
    assert response.status_code == status_code
    assert type(response.content) is bytes
    assert "text/csv" in response.headers["content-type"]
    if goals_qty:
        assert len(response.content) > 2
        assert int(response.headers["content-length"]) > 1
