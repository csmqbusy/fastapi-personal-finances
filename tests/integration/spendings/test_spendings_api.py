import json
from datetime import datetime
from itertools import cycle
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.models import UserModel
from app.repositories import user_spend_cat_repo
from app.schemas.transaction_category_schemas import TransactionsOnDeleteActions
from app.schemas.transactions_schemas import STransactionResponse
from app.services import user_spend_cat_service, spendings_service
from tests.factories import (
    UsersSpendingCategoriesFactory,
    SpendingsFactory,
    STransactionUpdateFactory,
    STransactionCreateFactory,
)
from tests.helpers import (
    add_obj_to_db,
    add_obj_to_db_all,
    auth_another_user,
    create_batch,
    create_n_categories,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "amount, category_name, create_category, status_code",
    [
        (100, None, False, status.HTTP_201_CREATED),
        (100, "Food", True, status.HTTP_201_CREATED),
        (100, "Food", False, status.HTTP_404_NOT_FOUND),
        (-100, "Food", True, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (None, "Food", True, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ]
)
async def test_spendings__post(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    amount: int | None,
    category_name: str | None,
    create_category: bool,
    status_code: int,
):
    if create_category:
        category = UsersSpendingCategoriesFactory(
            user_id=auth_user.id, category_name=category_name,
        )
        await add_obj_to_db(category, db_session)

    response = await client.post(
        url=f"{settings.api.prefix_v1}/spendings/",
        json={
            "amount": amount,
            "category_name": category_name,
        }
    )
    assert response.status_code == status_code
    if status_code == status.HTTP_201_CREATED:
        assert STransactionResponse.model_validate(response.json())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "num_of_categories",
    [5, 200, 0],
)
async def test_spendings_categories__get(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    num_of_categories: int,
):
    categories = [UsersSpendingCategoriesFactory(user_id=auth_user.id)
                  for _ in range(num_of_categories)]
    await add_obj_to_db_all(categories, db_session)

    categories_response = await client.get(
        url=f"{settings.api.prefix_v1}/spendings/categories/",
    )
    assert categories_response.status_code == status.HTTP_200_OK
    assert type(categories_response.json()) is list
    # +1 is an automatically created category for the rest spendings
    assert len(categories_response.json()) == len(categories) + 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_spending_id, sign_in_another_user, status_code",
    [
        (None, False, status.HTTP_200_OK),
        (99999, False, status.HTTP_404_NOT_FOUND),
        (None, True, status.HTTP_404_NOT_FOUND),
    ]
)
async def test_spendings_spending_id__get(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    wrong_spending_id: int | None,
    sign_in_another_user: bool,
    status_code: int,
):
    category = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    await add_obj_to_db(category, db_session)
    spending = SpendingsFactory(user_id=auth_user.id, category_id=category.id)
    await add_obj_to_db(spending, db_session)

    if sign_in_another_user:
        await auth_another_user(db_session, client)

    spending_id = wrong_spending_id or spending.id
    response = await client.get(
        url=f"{settings.api.prefix_v1}/spendings/{spending_id}/",
    )
    assert response.status_code == status_code


@pytest.mark.asyncio
async def test_spendings_spending_id__patch__success(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
):
    new_cat = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    await add_obj_to_db(new_cat, db_session)
    spending = SpendingsFactory(user_id=auth_user.id, category_id=new_cat.id)
    await add_obj_to_db(spending, db_session)

    update_obj = STransactionUpdateFactory(category_name=new_cat.category_name)
    response = await client.patch(
        url=f"{settings.api.prefix_v1}/spendings/{spending.id}/",
        content=update_obj.model_dump_json(),
    )

    assert response.status_code == status.HTTP_200_OK
    update_obj_as_response = json.loads(update_obj.model_dump_json())
    assert update_obj_as_response.items() <= response.json().items()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_category_name, wrong_spending_id, sign_in_another_user",
    [
        (None, 99999, False),
        ("wrong", None, False),
        (None, None, True),
    ]
)
async def test_spendings_spending_id__patch__error(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    wrong_category_name: str | None,
    wrong_spending_id: int | None,
    sign_in_another_user: bool,
):
    new_cat = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    await add_obj_to_db(new_cat, db_session)

    spending = await spendings_service.add_transaction_to_db(
        STransactionCreateFactory(),
        auth_user.id,
        db_session,
    )
    spending_id = wrong_spending_id or spending.id

    if sign_in_another_user:
        await auth_another_user(db_session, client)

    update_obj = STransactionUpdateFactory(
        category_name=wrong_category_name or new_cat.category_name,
    )
    response = await client.patch(
        url=f"{settings.api.prefix_v1}/spendings/{spending_id}/",
        content=update_obj.model_dump_json(),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_spendings_spending_id__delete__success(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
):
    spending = await spendings_service.add_transaction_to_db(
        STransactionCreateFactory(),
        auth_user.id,
        db_session,
    )
    response = await client.delete(
        url=f"{settings.api.prefix_v1}/spendings/{spending.id}/",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == spending.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "wrong_spending_id, sign_in_another_user, status_code",
    [
        (99999, False, status.HTTP_404_NOT_FOUND),
        (None, True, status.HTTP_404_NOT_FOUND),
    ]
)
async def test_spendings_spending_id__delete__error(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    wrong_spending_id: int | None,
    sign_in_another_user: bool,
    status_code: int,
):
    category = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    await add_obj_to_db(category, db_session)

    spending = await spendings_service.add_transaction_to_db(
        STransactionCreateFactory(),
        auth_user.id,
        db_session,
    )
    spending_id = wrong_spending_id or spending.id

    if sign_in_another_user:
        await auth_another_user(db_session, client)

    response = await client.delete(
        url=f"{settings.api.prefix_v1}/spendings/{spending_id}/",
    )
    assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_params, wrong_category_name, status_code",
    [
        (
            {
                "description_search_term": "text",
                "min_amount": 500,
                "max_amount": 500000,
                "datetime_from": datetime(year=2015, month=1, day=1),
                "datetime_to": datetime(year=2030, month=1, day=1),
                "page_size": 5,
                "page": 2,
                "sort_param": "amount",
            },
            None,
            status.HTTP_200_OK,
        ),
        (
            {},
            "wrong",
            status.HTTP_404_NOT_FOUND,
        ),
    ]
)
async def test_spendings__get(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    request_params: dict[str, Any],
    wrong_category_name: str | None,
    status_code: int,
):
    spendings_qty = 30
    category = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    await add_obj_to_db(category, db_session)

    add_params = dict(
        description=request_params.get("description_search_term"),
        category_id=category.id,
        user_id=auth_user.id,
    )
    await create_batch(db_session, spendings_qty, SpendingsFactory, add_params)

    request_params["category_name"] = wrong_category_name or category.category_name
    response = await client.get(
        url=f"{settings.api.prefix_v1}/spendings/",
        params=request_params,
    )

    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK:
        assert len(response.json()) == request_params["page_size"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "spendings_qty",
    [30, 0],
)
async def test_spendings__get_csv(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    spendings_qty: int,
):
    category = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    await add_obj_to_db(category, db_session)

    add_params = dict(category_id=category.id, user_id=auth_user.id)
    await create_batch(db_session, spendings_qty, SpendingsFactory, add_params)

    response = await client.get(
        url=f"{settings.api.prefix_v1}/spendings/",
        params={"in_csv": True}
    )
    assert response.status_code == status.HTTP_200_OK
    assert type(response.content) is bytes
    assert "text/csv" in response.headers["content-type"]
    if spendings_qty:
        assert len(response.content) > 2
        assert int(response.headers["content-length"]) > 1


@pytest.mark.asyncio
async def test_spendings_categories__post__success(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
):
    response = await client.post(
        url=f"{settings.api.prefix_v1}/spendings/categories/",
        json={"category_name": "any_name"}
    )
    categories = await user_spend_cat_service.get_user_categories(
        auth_user.id, db_session,
    )
    assert response.status_code == status.HTTP_201_CREATED
    # +1 is an automatically created category for the rest spendings
    assert len(categories) == 1 + 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, try_add_again, status_code",
    [
        ("Balls", True, status.HTTP_409_CONFLICT),
        (None, False, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ("", False, status.HTTP_422_UNPROCESSABLE_ENTITY),
        (" ", False, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ]
)
async def test_spendings_categories__post__error(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    category_name: str | None,
    try_add_again: bool,
    status_code: int,
):
    for _ in range(1 + try_add_again):
        response = await client.post(
            url=f"{settings.api.prefix_v1}/spendings/categories/",
            json={"category_name": category_name}
        )

    categories = await user_spend_cat_service.get_user_categories(
        auth_user.id, db_session,
    )
    assert response.status_code == status_code
    if response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY:
        assert len(categories) == 1 + 1


@pytest.mark.asyncio
async def test_spendings_categories__patch__success(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
):
    new_category_name = "new name"
    category_1 = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    await add_obj_to_db(category_1, db_session)

    created_category = await user_spend_cat_repo.get(db_session, category_1.id)
    assert created_category.category_name != new_category_name

    response = await client.patch(
        url=f"{settings.api.prefix_v1}/spendings/categories/{category_1.category_name}/",
        json={"category_name": new_category_name}
    )
    assert response.status_code == status.HTTP_200_OK

    updated_category = await user_spend_cat_repo.get(db_session, category_1.id)
    await db_session.refresh(updated_category)

    assert updated_category.category_name == new_category_name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_category_1, create_category_2, status_code",
    [
        (False, False, status.HTTP_404_NOT_FOUND),
        (True, True, status.HTTP_409_CONFLICT),
    ]
)
async def test_spendings_categories__patch__error(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    create_category_1: bool,
    create_category_2: bool,
    status_code: int,
):
    category_1 = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    if create_category_1:
        await add_obj_to_db(category_1, db_session)
    category_2 = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    if create_category_2:
        await add_obj_to_db(category_2, db_session)

    response = await client.patch(
        url=f"{settings.api.prefix_v1}/spendings/categories/{category_1.category_name}/",
        json={
            "category_name": category_2.category_name,
        }
    )
    assert response.status_code == status_code


@pytest.mark.asyncio
async def test_spendings_categories__delete__success(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
):
    category = UsersSpendingCategoriesFactory(user_id=auth_user.id)
    await add_obj_to_db(category, db_session)

    response = await client.delete(
        url=f"{settings.api.prefix_v1}/spendings/categories/{category.category_name}/",
        params={
            "handle_spendings_on_deletion": TransactionsOnDeleteActions.DELETE,
        }
    )
    assert response.status_code == status.HTTP_200_OK

    categories = await user_spend_cat_service.get_user_categories(
        auth_user.id, db_session,
    )
    categories = [i.category_name for i in categories]
    assert category.category_name not in categories


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, create_category, on_delete_action, status_code",
    [
        (
            "Balls",
            False,
            TransactionsOnDeleteActions.DELETE,
            status.HTTP_404_NOT_FOUND,
        ),
        (
            settings.app.default_spending_category_name,
            False,
            TransactionsOnDeleteActions.DELETE,
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "Balls",
            True,
            TransactionsOnDeleteActions.TO_NEW_CAT,
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "Balls",
            True,
            TransactionsOnDeleteActions.TO_EXISTS_CAT,
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "Balls",
            True,
            None,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    ]
)
async def test_spendings_categories__delete__error(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    category_name: str,
    create_category: bool,
    on_delete_action: TransactionsOnDeleteActions,
    status_code: int,
):
    if create_category:
        category = UsersSpendingCategoriesFactory(
            user_id=auth_user.id, category_name=category_name,
        )
        await add_obj_to_db(category, db_session)

    response = await client.delete(
        url=f"{settings.api.prefix_v1}/spendings/categories/{category_name}/",
        params={
            "handle_spendings_on_deletion": on_delete_action,
        }
    )
    assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "request_params",
        "expected_summary_amount",
        "wrong_category_name",
        "status_code",
    ),
    [
        (
            {
                "min_amount": 1000,
                "max_amount": 9000,
                "datetime_from": datetime(year=2020, month=1, day=1),
                "datetime_to": datetime(year=2030, month=1, day=1),
            },
            [12000, 15000, 18000],
            None,
            status.HTTP_200_OK,
        ),
        (
            {},
            None,
            "wrong_category_name",
            status.HTTP_404_NOT_FOUND,
        ),
    ]
)
async def test_spendings_summary_get__get(
    db_session: AsyncSession,
    client: AsyncClient,
    auth_user: UserModel,
    request_params: dict[str, Any],
    expected_summary_amount: list[int],
    wrong_category_name: str | None,
    status_code: int,
):
    amounts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000]
    datetimes = [datetime(year=2020 + i, month=1, day=1, hour=12) for i in range(9)]
    categories_ids = await create_n_categories(3, auth_user.id, db_session)

    for amount, dt, cat_id in zip(amounts, datetimes, cycle(categories_ids)):
        spending = SpendingsFactory(
            amount=amount,
            date=dt,
            user_id=auth_user.id,
            category_id=cat_id,
        )
        await add_obj_to_db(spending, db_session)

    if wrong_category_name:
        request_params["category_name"] = wrong_category_name
    else:
        request_params["category_id"] = categories_ids
    response = await client.get(
        url=f"{settings.api.prefix_v1}/spendings/summary/",
        params=request_params,
    )
    assert response.status_code == status_code
    if not wrong_category_name:
        response_amounts = sorted(i["amount"] for i in response.json())
        expected_summary_amount.sort()
        assert response_amounts == expected_summary_amount
