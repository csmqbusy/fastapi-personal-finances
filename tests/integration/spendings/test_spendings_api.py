from contextlib import nullcontext
from datetime import datetime
from typing import ContextManager

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.testclient import TestClient

from app.core.config import settings
from app.schemas.transactions_schemas import STransactionResponse, \
    STransactionUpdatePartial
from app.services import user_spend_cat_service
from app.services.user_service import get_user_by_username
from tests.integration.helpers import sign_up_user, sign_in_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "status_code",
        "amount",
        "category_name",
        "create_category",
        "expectation",
    ),
    [
        (
            "Salah10",
            status.HTTP_201_CREATED,
            100,
            None,
            False,
            nullcontext(),
        ),
        (
            "Salah20",
            status.HTTP_201_CREATED,
            100,
            "Food",
            True,
            nullcontext(),
        ),
        (
            "Salah30",
            status.HTTP_404_NOT_FOUND,
            100,
            "Food",
            False,
            pytest.raises(ValidationError),
        ),
        (
            "Salah40",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            -100,
            "Food",
            True,
            pytest.raises(ValidationError),
        ),
        (
            "Salah50",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            None,
            "Food",
            True,
            pytest.raises(ValidationError),
        ),
    ]
)
async def test_spendings__post(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    status_code: int,
    amount: int | None,
    category_name: str,
    create_category: bool,
    expectation: ContextManager,
):
    sign_up_user(client, username)
    sign_in_user(client, username)
    user = await get_user_by_username(username, db_session)

    if create_category:
        await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )

    response = client.post(
        url=f"{settings.api.prefix_v1}/spendings/",
        json={
            "amount": amount,
            "category_name": category_name,
        }
    )
    assert response.status_code == status_code
    with expectation:
        response_schema = STransactionResponse.model_validate(response.json())
        assert type(response_schema) is STransactionResponse


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "categories",
        "status_code",
    ),
    [
        (
            "Messi10",
            ["Balls", "Games", "Food", "Doping"],
            status.HTTP_200_OK,
        ),
        (
            "Messi20",
            [],
            status.HTTP_200_OK,
        ),
        (
            "Messi30",
            [f"Category_{i}" for i in range(200)],
            status.HTTP_200_OK,
        ),
    ]
)
async def test_spendings_categories__get(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    categories: list[str],
    status_code: int,
):
    sign_up_user(client, username)
    sign_in_user(client, username)
    user = await get_user_by_username(username, db_session)

    for category_name in categories:
        await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )

    categories_response = client.get(
        url=f"{settings.api.prefix_v1}/spendings/categories/",
    )
    assert categories_response.status_code == status_code
    # +1 is an automatically created category for the rest spendings
    assert len(categories_response.json()) == len(categories) + 1

    assert type(categories_response.json()) is list
    categories.append(settings.app.default_spending_category_name)
    for category in categories_response.json():
        assert category["category_name"] in categories


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "amount",
        "wrong_spending_id",
        "sign_in_another_user",
        "status_code",
    ),
    [
        (
            "Ronaldo10",
            800,
            False,
            False,
            status.HTTP_200_OK,
        ),
        (
            "Ronaldo20",
            300,
            True,
            False,
            status.HTTP_404_NOT_FOUND,
        ),
        (
            "Ronaldo30",
            500,
            False,
            True,
            status.HTTP_404_NOT_FOUND,
        ),
    ]
)
async def test_spendings_spending_id__get(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    amount: int,
    wrong_spending_id: bool,
    sign_in_another_user: bool,
    status_code: int,
):
    sign_up_user(client, username)
    sign_in_user(client, username)

    response = client.post(
        url=f"{settings.api.prefix_v1}/spendings/",
        json={
            "amount": 800,
        }
    )
    spending_id = response.json()["id"] + wrong_spending_id

    if sign_in_another_user:
        another_username = f"Another{username}"
        sign_up_user(client, another_username)
        sign_in_user(client, another_username)

    categories_response = client.get(
        url=f"{settings.api.prefix_v1}/spendings/{spending_id}/",
    )
    assert categories_response.status_code == status_code
    if categories_response.status_code == status.HTTP_200_OK:
        assert categories_response.json()["amount"] == amount


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "new_amount",
        "new_description",
        "new_date",
        "new_category_name",
        "create_category",
        "wrong_spending_id",
        "sign_in_another_user",
        "status_code",
    ),
    [
        (
            "Aguero10",
            8090,
            "new description",
            datetime(year=2020, month=12, day=31),
            "new category",
            True,
            False,
            False,
            status.HTTP_200_OK,
        ),
        (
            "Aguero20",
            3000,
            "new description",
            datetime(year=2020, month=12, day=31),
            "new category",
            True,
            True,
            False,
            status.HTTP_404_NOT_FOUND,
        ),
        (
            "Aguero30",
            3000,
            "new description",
            datetime(year=2020, month=12, day=31),
            "new category",
            True,
            False,
            True,
            status.HTTP_404_NOT_FOUND,
        ),
        (
            "Aguero40",
            3000,
            "new description",
            datetime(year=2020, month=12, day=31),
            "new category",
            False,
            False,
            False,
            status.HTTP_404_NOT_FOUND,
        ),
    ]
)
async def test_spendings_spending_id__patch(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    new_amount: int,
    new_description: str,
    new_date: datetime,
    new_category_name: str,
    create_category: bool,
    wrong_spending_id: bool,
    sign_in_another_user: bool,
    status_code: int,
):
    sign_up_user(client, username)
    sign_in_user(client, username)
    user = await get_user_by_username(username, db_session)

    if create_category:
        await user_spend_cat_service.add_category_to_db(
            user.id,
            new_category_name,
            db_session,
        )

    response = client.post(
        url=f"{settings.api.prefix_v1}/spendings/",
        json={
            "amount": 800,
        }
    )
    spending_id = response.json()["id"] + wrong_spending_id

    if sign_in_another_user:
        another_username = f"Another{username}"
        sign_up_user(client, another_username)
        sign_in_user(client, another_username)

    update_obj = STransactionUpdatePartial(
        amount=new_amount,
        description=new_description,
        date=new_date,
        category_name=new_category_name,
    )
    request_json = update_obj.model_dump_json()
    response = client.patch(
        url=f"{settings.api.prefix_v1}/spendings/{spending_id}/",
        content=request_json,
    )

    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json()["amount"] == new_amount
        assert response.json()["description"] == new_description
        response_parsed_datetime = datetime.strptime(
            response.json()["date"],
            "%Y-%m-%dT%H:%M:%S",
        )
        assert response_parsed_datetime == new_date
        assert response.json()["category_name"] == new_category_name
