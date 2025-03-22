from datetime import date, datetime
from random import choice, randint

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel
from app.repositories import spendings_repo
from app.schemas.common_schemas import SortParam
from tests.factories import SpendingsFactory, UsersSpendingCategoriesFactory
from tests.helpers import (
    add_obj_to_db,
    create_n_categories,
    create_test_spendings,
)


@pytest.mark.asyncio
async def test_get_transaction_with_category(
    db_session: AsyncSession,
    user: UserModel,
) -> None:
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)

    spending = SpendingsFactory(user_id=user.id, category_id=category.id)
    await add_obj_to_db(spending, db_session)

    spending_from_db = await spendings_repo.get_transaction_with_category(
        db_session,
        spending.id,
    )
    assert spending_from_db.category.id == category.id
    assert spending_from_db.category.category_name == category.category_name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "prices",
    [
        ([200, 500, 400, 100, 300, 900]),
    ],
)
async def test_get_transactions_from_db__with_sort(
    db_session: AsyncSession,
    user: UserModel,
    prices: list[int],
) -> None:
    categories_ids = await create_n_categories(randint(1, 5), user.id, db_session)

    for price in prices:
        spending = SpendingsFactory(
            amount=price,
            user_id=user.id,
            category_id=choice(categories_ids),
        )
        await add_obj_to_db(spending, db_session)

    spendings = await spendings_repo.get_transactions_from_db(
        user_id=user.id,
        session=db_session,
        categories_ids=categories_ids,
        sort_params=[SortParam(order_by="amount", order_direction="asc")],
    )
    assert len(spendings) == len(prices)
    assert [s.amount for s in spendings] == sorted(prices)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "datetime_from, datetime_to, expected_spendings_qty",
    [
        (
            datetime(year=2020, month=1, day=11, hour=12, minute=0),
            datetime(year=2021, month=1, day=11, hour=12, minute=0),
            3,
        ),
    ],
)
async def test_get_transactions_from_db__with_datetime_period(
    db_session: AsyncSession,
    user: UserModel,
    datetime_from: datetime,
    datetime_to: datetime,
    expected_spendings_qty: int,
) -> None:
    datetimes = [
        datetime(year=2020, month=1, day=11, hour=11, minute=59),
        datetime(year=2020, month=1, day=11, hour=12, minute=0),
        datetime(year=2021, month=1, day=11, hour=12, minute=0),
        datetime(year=2021, month=1, day=11, hour=12, minute=0),
        datetime(year=2021, month=1, day=11, hour=12, minute=1),
    ]
    categories_ids = await create_n_categories(3, user.id, db_session)

    for dt in datetimes:
        spending = SpendingsFactory(
            date=dt,
            user_id=user.id,
            category_id=choice(categories_ids),
        )
        await add_obj_to_db(spending, db_session)

    spendings = await spendings_repo.get_transactions_from_db(
        user_id=user.id,
        session=db_session,
        categories_ids=categories_ids,
        datetime_from=datetime_from,
        datetime_to=datetime_to,
    )
    assert len(spendings) == expected_spendings_qty
    for sp in spendings:
        assert sp.date >= datetime_from
        assert sp.date <= datetime_to


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "search_term, expected_spendings_qty",
    [
        ("Food", 5),
    ],
)
async def test_get_transactions_from_db__with_desc_search_term(
    db_session: AsyncSession,
    user: UserModel,
    search_term: str,
    expected_spendings_qty: int,
) -> None:
    descriptions = [
        "Cat Food",
        "dog food",
        "turtle foOd",
        "turtle sneakers",
        "Dog toys",
        "Food for cat",
        "delicious food for dog",
    ]
    categories_ids = await create_n_categories(3, user.id, db_session)

    for description in descriptions:
        spending = SpendingsFactory(
            description=description,
            user_id=user.id,
            category_id=choice(categories_ids),
        )
        await add_obj_to_db(spending, db_session)

    spendings = await spendings_repo.get_transactions_from_db(
        user_id=user.id,
        session=db_session,
        description_search_term=search_term,
    )
    assert len(spendings) == expected_spendings_qty
    for sp in spendings:
        assert search_term.lower() in sp.description.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "min_amount, max_amount, expected_spendings_qty",
    [
        (800, 2000, 5),
        (100000, 100001, 1),
        (0, 10, 1),
        (100001, 1000000, 0),
    ],
)
async def test_get_transactions_from_db__with_amount_range(
    db_session: AsyncSession,
    user: UserModel,
    min_amount: int,
    max_amount: int,
    expected_spendings_qty: int,
) -> None:
    amounts = [10, 200, 800, 1200, 1600, 2000, 20000, 100000, 3000, 1500]
    categories_ids = await create_n_categories(randint(1, 5), user.id, db_session)

    for amount in amounts:
        spending = SpendingsFactory(
            amount=amount,
            user_id=user.id,
            category_id=choice(categories_ids),
        )
        await add_obj_to_db(spending, db_session)

    spendings = await spendings_repo.get_transactions_from_db(
        user_id=user.id,
        session=db_session,
        categories_ids=categories_ids,
        min_amount=min_amount,
        max_amount=max_amount,
    )
    assert len(spendings) == expected_spendings_qty
    for sp in spendings:
        assert min_amount <= sp.amount <= max_amount


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "min_amount",
        "max_amount",
        "search_term",
        "datetime_from",
        "datetime_to",
        "expected_spendings_qty",
    ),
    [
        (
            2000,
            10000,
            "text",
            datetime(year=2022, month=2, day=2),
            datetime(year=2023, month=1, day=1),
            2,
        ),
        (
            3000,
            7000,
            "XT",
            datetime(year=2022, month=1, day=1),
            datetime(year=2024, month=1, day=1),
            4,
        ),
    ],
)
async def test_get_transactions_from_db__with_all_filters(
    db_session: AsyncSession,
    user: UserModel,
    min_amount: int,
    max_amount: int,
    search_term: str,
    datetime_from: datetime,
    datetime_to: datetime,
    expected_spendings_qty: int,
) -> None:
    amounts = [1000, 2000, 3000, 4000, 5000, 7000]
    descriptions = ["text", "TEXT ", "My Text", "text1", "text2", "t3xt"]
    datetimes = [
        datetime(year=2020, month=1, day=1),
        datetime(year=2021, month=1, day=1),
        datetime(year=2022, month=1, day=1),
        datetime(year=2023, month=1, day=1),
        datetime(year=2023, month=1, day=1),
        datetime(year=2024, month=1, day=1),
    ]
    categories_ids = await create_n_categories(randint(1, 5), user.id, db_session)

    for amount, description, dt in zip(amounts, descriptions, datetimes):
        spending = SpendingsFactory(
            amount=amount,
            description=description,
            date=dt,
            user_id=user.id,
            category_id=choice(categories_ids),
        )
        await add_obj_to_db(spending, db_session)

    spendings = await spendings_repo.get_transactions_from_db(
        user_id=user.id,
        categories_ids=categories_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        description_search_term=search_term,
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        sort_params=[SortParam(order_by="amount", order_direction="desc")],
        session=db_session,
    )
    spendings_amount = [s.amount for s in spendings]
    assert len(spendings) == expected_spendings_qty
    assert spendings_amount == sorted(spendings_amount, reverse=True)


async def test_get_annual_summary_from_db(
    db_session: AsyncSession,
    user: UserModel,
) -> None:
    num_of_cats = 3
    await create_test_spendings(
        db_session, user.id, num_of_categories=num_of_cats
    )

    summary = await spendings_repo.get_annual_summary_from_db(
        db_session,
        user.id,
        date.today().year,
    )
    assert summary
    assert num_of_cats <= len(summary) <= num_of_cats * 12
    assert len(summary[0]) == 3
    assert len(summary[-1]) == 3


async def test_get_monthly_summary_from_db(
    db_session: AsyncSession,
    user: UserModel,
) -> None:
    num_of_cats = 4
    await create_test_spendings(
        db_session,
        user.id,
        spendings_date_range="this_month",
        spendings_qty=100,
        num_of_categories=num_of_cats,
    )

    summary = await spendings_repo.get_monthly_summary_from_db(
        db_session,
        user.id,
        date.today().year,
        date.today().month,
    )
    assert summary
    assert 1 <= len(summary) <= num_of_cats * 31
    assert len(summary[0]) == 3
    assert len(summary[-1]) == 3
