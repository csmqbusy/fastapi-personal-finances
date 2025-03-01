from contextlib import nullcontext
from datetime import datetime
from typing import ContextManager

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.testclient import TestClient

from app.core.config import settings
from app.schemas.transaction_category_schemas import TransactionsOnDeleteActions
from app.schemas.transactions_schemas import (
    STransactionResponse,
    STransactionUpdatePartial,
)
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "new_category_name",
        "create_category",
        "wrong_spending_id",
        "sign_in_another_user",
        "status_code",
    ),
    [
        (
            "Balotelli10",
            "new category",
            True,
            False,
            False,
            status.HTTP_200_OK,
        ),
        (
            "Balotelli20",
            "new category",
            True,
            True,
            False,
            status.HTTP_404_NOT_FOUND,
        ),
        (
            "Balotelli30",
            "new category",
            True,
            False,
            True,
            status.HTTP_404_NOT_FOUND,
        ),
    ]
)
async def test_spendings_spending_id__delete(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
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
            "category_name": new_category_name,
        }
    )
    spending_id = response.json()["id"] + wrong_spending_id

    if sign_in_another_user:
        another_username = f"Another{username}"
        sign_up_user(client, another_username)
        sign_in_user(client, another_username)

    response = client.delete(
        url=f"{settings.api.prefix_v1}/spendings/{spending_id}/",
    )

    assert response.status_code == status_code
    if status_code == status.HTTP_200_OK:
        assert response.json()["id"] == spending_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "category_name",
        "wrong_category_name",
        "spendings_qty",
        "description",
        "amount_start",
        "amount_step",
        "year_start",
        "min_amount",
        "max_amount",
        "datetime_from",
        "datetime_to",
        "page_size",
        "page",
        "sort_param",
        "reversed_sort_param",
        "status_code",
    ),
    [
        (
            "Lukaku10",
            "Food",
            False,
            30,
            "text",
            500,
            50,
            2010,
            500,
            500000,
            datetime(year=2015, month=1, day=1),
            datetime(year=2030, month=1, day=1),
            5,
            2,
            "amount",
            "-amount",
            status.HTTP_200_OK,
        ),
        (
            "Lukaku20",
            "Food",
            True,
            30,
            "text",
            500,
            50,
            2010,
            500,
            500000,
            datetime(year=2015, month=1, day=1),
            datetime(year=2030, month=1, day=1),
            5,
            2,
            "amount",
            "-amount",
            status.HTTP_404_NOT_FOUND,
        ),
    ]
)
async def test_spendings__get(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    category_name: str,
    wrong_category_name: bool,
    spendings_qty: int,
    description: str,
    amount_start: int,
    amount_step: int,
    year_start: int,
    min_amount: int,
    max_amount: int,
    datetime_from: datetime,
    datetime_to: datetime,
    page_size: int,
    page: int,
    sort_param: str,
    reversed_sort_param: str,
    status_code: int,
):
    sign_up_user(client, username)
    sign_in_user(client, username)
    user = await get_user_by_username(username, db_session)

    await user_spend_cat_service.add_category_to_db(
        user.id,
        category_name,
        db_session,
    )
    for i in range(spendings_qty):
        client.post(
            url=f"{settings.api.prefix_v1}/spendings/",
            json={
                "amount": amount_start + (amount_step * i),
                "category_name": category_name,
                "description": description,
                "date": datetime(
                    year=year_start + i, month=1, day=1
                    ).isoformat(),
            }
        )

    response = client.get(
        url=f"{settings.api.prefix_v1}/spendings/",
        params={
            "category_name": category_name if not wrong_category_name else "wc",
            "datetime_from": datetime_from,
            "datetime_to": datetime_to,
            "page_size": page_size,
            "page": page,
            "sort_params": sort_param,
            "description_search_term": description,
            "min_amount": min_amount,
            "max_amount": max_amount,
        },
    )

    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK:
        assert len(response.json()) == page_size

        reversed_response = client.get(
            url=f"{settings.api.prefix_v1}/spendings/",
            params={
                "category_name": category_name if not wrong_category_name else "wc",
                "datetime_from": datetime_from,
                "datetime_to": datetime_to,
                "page_size": page_size,
                "page": page,
                "sort_params": reversed_sort_param,
            },
        )

        assert response.json() != reversed_response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "category_name",
        "try_add_again",
        "status_code",
    ),
    [
        (
            "Larsson10",
            "Balls",
            False,
            status.HTTP_201_CREATED,
        ),
        (
            "Larsson20",
            "Balls",
            True,
            status.HTTP_409_CONFLICT,
        ),
        (
            "Larsson30",
            None,
            False,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            "Larsson40",
            "",
            False,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            "Larsson50",
            " ",
            False,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    ]
)
async def test_spendings_categories__post(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    category_name: str,
    try_add_again: bool,
    status_code: int,
):
    sign_up_user(client, username)
    sign_in_user(client, username)

    response = client.post(
        url=f"{settings.api.prefix_v1}/spendings/categories/",
        json={
            "category_name": category_name,
        }
    )
    if try_add_again:
        response = client.post(
            url=f"{settings.api.prefix_v1}/spendings/categories/",
            json={
                "category_name": category_name,
            }
        )

    categories_response = client.get(
        url=f"{settings.api.prefix_v1}/spendings/categories/",
    )

    assert response.status_code == status_code
    if response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY:
        assert len(categories_response.json()) == 1 + 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "category_name_1",
        "create_category_1",
        "category_name_2",
        "category_name_3",
        "status_code",
    ),
    [
        (
            "Ibrahimovic10",
            "Balls",
            True,
            "New balls",
            None,
            status.HTTP_200_OK,
        ),
        (
            "Ibrahimovic20",
            "Balls",
            False,
            "New balls",
            None,
            status.HTTP_404_NOT_FOUND,
        ),
        (
            "Ibrahimovic30",
            "One Balls",
            True,
            "Two balls",
            "Three balls",
            status.HTTP_409_CONFLICT,
        ),
    ]
)
async def test_spendings_categories__patch(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    category_name_1: str,
    create_category_1: bool,
    category_name_2: str,
    category_name_3: str | None,
    status_code: int,
):
    sign_up_user(client, username)
    sign_in_user(client, username)

    if create_category_1:
        client.post(
            url=f"{settings.api.prefix_v1}/spendings/categories/",
            json={
                "category_name": category_name_1,
            }
        )
    if category_name_3:
        client.post(
            url=f"{settings.api.prefix_v1}/spendings/categories/",
            json={
                "category_name": category_name_3,
            }
        )

    if create_category_1:
        categories_response = client.get(
            url=f"{settings.api.prefix_v1}/spendings/categories/",
        )
        categories = [i["category_name"] for i in categories_response.json()]
        assert category_name_1 in categories

    response = client.patch(
        url=f"{settings.api.prefix_v1}/spendings/categories/{category_name_1}/",
        json={
            "category_name": category_name_3 or category_name_2,
        }
    )
    assert response.status_code == status_code

    if response.status_code == status.HTTP_200_OK:
        categories_response = client.get(
            url=f"{settings.api.prefix_v1}/spendings/categories/",
        )
        categories = [i["category_name"] for i in categories_response.json()]
        assert category_name_2 in categories
        assert category_name_1 not in categories


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "category_name",
        "create_category",
        "new_category_name",
        "on_delete_action",
        "status_code",
    ),
    [
        (
            "Arshavin10",
            "Balls",
            True,
            None,
            TransactionsOnDeleteActions.DELETE,
            status.HTTP_200_OK,
        ),
        (
            "Arshavin20",
            " Balls ",
            True,
            None,
            TransactionsOnDeleteActions.DELETE,
            status.HTTP_200_OK,
        ),
        (
            "Arshavin30",
            settings.app.default_spending_category_name,
            True,
            None,
            TransactionsOnDeleteActions.DELETE,
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "Arshavin40",
            "Balls",
            False,
            None,
            TransactionsOnDeleteActions.DELETE,
            status.HTTP_404_NOT_FOUND,
        ),
        (
            "Arshavin50",
            "Balls",
            True,
            None,
            TransactionsOnDeleteActions.TO_NEW_CAT,
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "Arshavin60",
            "Balls",
            True,
            None,
            TransactionsOnDeleteActions.TO_EXISTS_CAT,
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "Arshavin70",
            "Balls",
            True,
            None,
            None,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            "Arshavin80",
            None,
            True,
            None,
            None,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
        (
            "Arshavin90",
            None,
            False,
            None,
            None,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    ]
)
async def test_spendings_categories__delete(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    category_name: str,
    create_category: bool,
    new_category_name: str | None,
    on_delete_action: TransactionsOnDeleteActions,
    status_code: int,
):
    sign_up_user(client, username)
    sign_in_user(client, username)

    if create_category:
        client.post(
            url=f"{settings.api.prefix_v1}/spendings/categories/",
            json={
                "category_name": category_name,
            }
        )

    response = client.delete(
        url=f"{settings.api.prefix_v1}/spendings/categories/{category_name}/",
        params={
            "handle_spendings_on_deletion": on_delete_action,
        }
    )

    assert response.status_code == status_code

    if response.status_code == status.HTTP_200_OK:
        categories_response = client.get(
            url=f"{settings.api.prefix_v1}/spendings/categories/",
        )
        categories = [i["category_name"] for i in categories_response.json()]
        assert category_name not in categories


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "username",
        "categories_names",
        "spendings_qty",
        "amount",
        "year_start",
        "min_amount",
        "max_amount",
        "datetime_from",
        "datetime_to",
        "expected_summary_amount",
        "send_wrong_category",
        "status_code",
    ),
    [
        (
            "Lacazette10",
            ["Food", "Balls"],
            10,
            200,
            2010,
            200,
            200,
            datetime(year=2010, month=1, day=1),
            datetime(year=2030, month=1, day=1),
            [1000, 1000],
            False,
            status.HTTP_200_OK,
        ),
        (
            "Lacazette20",
            ["Food", "Balls", "Taxi", "Health", "Games"],
            50,
            200,
            2010,
            200,
            200,
            datetime(year=2017, month=1, day=1),
            datetime(year=2035, month=1, day=1),
            [800, 600, 800, 800, 800],
            False,
            status.HTTP_200_OK,
        ),
        (
            "Lacazette30",
            ["Food", "Balls"],
            10,
            200,
            2010,
            200,
            200,
            datetime(year=2010, month=1, day=1),
            datetime(year=2030, month=1, day=1),
            [1000, 1000],
            True,
            status.HTTP_404_NOT_FOUND,
        ),
    ]
)
async def test_spendings_summary_get__get(
    client: TestClient,
    db_session: AsyncSession,
    username: str,
    categories_names: list[str],
    spendings_qty: int,
    amount: int,
    year_start: int,
    min_amount: int,
    max_amount: int,
    datetime_from: datetime,
    datetime_to: datetime,
    expected_summary_amount: list[int],
    send_wrong_category: bool,
    status_code: int,
):
    sign_up_user(client, username)
    sign_in_user(client, username)
    user = await get_user_by_username(username, db_session)

    for category_name in categories_names:
        await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )
    for i in range(spendings_qty):
        client.post(
            url=f"{settings.api.prefix_v1}/spendings/",
            json={
                "amount": amount,
                "category_name": categories_names[i % len(categories_names)],
                "date": datetime(
                    year=year_start + i, month=1, day=1
                    ).isoformat(),
            }
        )

    response = client.get(
        url=f"{settings.api.prefix_v1}/spendings/summary/",
        params={
            "category_name": categories_names if not send_wrong_category else "wc",
            "datetime_from": datetime_from,
            "datetime_to": datetime_to,
            "min_amount": min_amount,
            "max_amount": max_amount,
        },
    )

    assert response.status_code == status_code
    if not send_wrong_category:
        response_amounts = sorted(i["amount"] for i in response.json())
        expected_summary_amount.sort()
        assert response_amounts == expected_summary_amount
