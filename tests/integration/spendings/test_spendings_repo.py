from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UsersSpendingCategoriesModel
from app.repositories import spendings_repo, user_repo
from app.schemas.transactions_schemas import STransactionCreateInDB
from app.schemas.common_schemas import SortParam
from app.services import user_spend_cat_service
from tests.integration.helpers import add_mock_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, create_user",
    [
        (
            "Balls",
            True,
        ),
        (
            "Doping",
            False,
        ),
    ]
)
async def test_get_transaction_with_category(
    db_session: AsyncSession,
    category_name: str,
    create_user: bool,
) -> None:
    mock_user_username = "GOLOVIN"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    category = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_name,
        db_session,
    )

    transaction_to_create = STransactionCreateInDB(
        amount=1000,
        description="Some description",
        date=None,
        user_id=user.id,
        category_id=category.id,
    )
    spending = await spendings_repo.add(
        db_session,
        transaction_to_create.model_dump(),
    )

    spending_from_db = await spendings_repo.get_transaction_with_category(
        db_session,
        spending.id,
    )
    assert type(spending_from_db.category) is UsersSpendingCategoriesModel
    assert spending_from_db.category.id == category.id
    assert spending_from_db.category.category_name == category.category_name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "categories_names, create_user, prices, sorted_prices",
    [
        (
            ["Food"],
            True,
            [200, 500, 400, 100, 300],
            [100, 200, 300, 400, 500],
        ),
        (
            ["Health", "Books", "Games"],
            False,
            [200, 500, 400, 100, 300, 900],
            [100, 200, 300, 400, 500, 900],
        ),
    ]
)
async def test_get_transactions__with_sort(
    db_session: AsyncSession,
    categories_names: list[str],
    create_user: bool,
    prices: list[int],
    sorted_prices: list[int],
) -> None:
    mock_user_username = "THURAM"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    categories_ids = []
    for category_name in categories_names:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )
        categories_ids.append(category.id)

    for i, p in enumerate(prices):
        transaction_to_create = STransactionCreateInDB(
            amount=p,
            description="Some description",
            date=None,
            user_id=user.id,
            category_id=categories_ids[i % len(categories_ids)],
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

    spendings = await spendings_repo.get_transactions_from_db(
        user_id=user.id,
        session=db_session,
        categories_ids=categories_ids,
        sort_params=[SortParam(order_by="amount", order_direction="asc")]
    )
    assert len(spendings) == len(prices)
    assert [s.amount for s in spendings] == sorted_prices


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "categories_names",
        "create_user",
        "datetimes",
        "datetime_from",
        "datetime_to",
        "expected_spendings_qty",
    ),
    [
        (
            ["Food", "Books"],
            True,
            [
                datetime(year=2020, month=1, day=11, hour=11, minute=59),
                datetime(year=2020, month=1, day=11, hour=12, minute=0),
                datetime(year=2020, month=1, day=11, hour=12, minute=1),
                datetime(year=2021, month=1, day=11, hour=12, minute=0),
                datetime(year=2021, month=1, day=11, hour=12, minute=1),
                datetime(year=2022, month=1, day=11, hour=12, minute=0),
            ],
            datetime(year=2020, month=1, day=11, hour=12, minute=0),
            datetime(year=2021, month=1, day=11, hour=12, minute=0),
            3,
        ),
    ]
)
async def test_get_transactions__with_datetime_period(
    db_session: AsyncSession,
    categories_names: list[str],
    create_user: bool,
    datetimes: list[datetime],
    datetime_from: datetime,
    datetime_to: datetime,
    expected_spendings_qty: int
) -> None:
    mock_user_username = "MARCUS"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    categories_ids = []
    for category_name in categories_names:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )
        categories_ids.append(category.id)

    for i, dt in enumerate(datetimes):
        transaction_to_create = STransactionCreateInDB(
            amount=999,
            description="Some description",
            date=dt,
            user_id=user.id,
            category_id=categories_ids[i % len(categories_ids)],
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

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
    (
        "categories_names",
        "create_user",
        "descriptions",
        "search_term",
        "expected_spendings_qty",
    ),
    [
        (
            ["Pets", "Casino"],
            True,
            [
                "Cat Food",
                "dog food",
                "turtle foOd",
                "Dog toys",
                "turtle sneakers",
                "Food for cat",
                "delicious food for dog",
            ],
            "Food",
            5,
        ),
    ]
)
async def test_get_transactions__with_desc_search_term(
    db_session: AsyncSession,
    categories_names: list[str],
    create_user: bool,
    descriptions: list[str],
    search_term: str,
    expected_spendings_qty: int
) -> None:
    mock_user_username = "DEGEA"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    categories_ids = []
    for category_name in categories_names:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )
        categories_ids.append(category.id)

    for i, description in enumerate(descriptions):
        transaction_to_create = STransactionCreateInDB(
            amount=333,
            description=description,
            date=None,
            user_id=user.id,
            category_id=categories_ids[i % len(categories_ids)],
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

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
    (
        "categories_names",
        "create_user",
        "amounts",
        "min_amount",
        "max_amount",
        "expected_spendings_qty",
    ),
    [
        (
            ["Pets"],
            True,
            [10, 200, 800, 1200, 1600, 2000, 20000, 100000, 3000, 1500],
            800,
            2000,
            5,
        ),
        (
            ["Games"],
            False,
            [10, 200, 800, 1200, 1600, 2000, 20000, 100000, 3000, 1500],
            100000,
            100001,
            1,
        ),
        (
            ["Food", "Books"],
            False,
            [10, 200, 800, 1200, 1600, 2000, 20000, 100000, 3000, 1500],
            0,
            10,
            1,
        ),
        (
            ["Health", "Casino"],
            False,
            [10, 200, 800, 1200, 1600, 2000, 20000, 100000, 3000, 1500],
            100001,
            1000000,
            0,
        ),
    ]
)
async def test_get_transactions__with_amount_range(
    db_session: AsyncSession,
    categories_names: list[str],
    create_user: bool,
    amounts: list[int],
    min_amount: int,
    max_amount: int,
    expected_spendings_qty: int
) -> None:
    mock_user_username = "ADARABIYO"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    categories_ids = []
    for category_name in categories_names:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )
        categories_ids.append(category.id)

    for i, amnt in enumerate(amounts):
        transaction_to_create = STransactionCreateInDB(
            amount=amnt,
            description=None,
            date=None,
            user_id=user.id,
            category_id=categories_ids[i % len(categories_ids)],
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

    spendings = await spendings_repo.get_transactions_from_db(
        user_id=user.id,
        session=db_session,
        categories_ids=categories_ids,
        min_amount=min_amount,
        max_amount=max_amount,
    )
    assert len(spendings) == expected_spendings_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "categories_names",
        "create_user",
        "amounts",
        "descriptions",
        "datetimes",
        "min_amount",
        "max_amount",
        "search_term",
        "datetime_from",
        "datetime_to",
        "sort_params",
        "expected_spendings_qty",
        "expected_amounts",
    ),
    [
        (
            ["Food", "Helth", "books"],
            True,
            [1000, 2000, 3000, 4000, 5000, 7000],
            ["text", "TEXT ", "My Text", "text1", "text2", "t3xt"],
            [
                datetime(year=2020, month=1, day=1),
                datetime(year=2021, month=1, day=1),
                datetime(year=2022, month=1, day=1),
                datetime(year=2023, month=1, day=1),
                datetime(year=2023, month=1, day=1),
                datetime(year=2024, month=1, day=1),
            ],
            2000,
            10000,
            "text",
            datetime(year=2022, month=2, day=2),
            datetime(year=2023, month=1, day=1),
            [SortParam(order_by="amount", order_direction="desc")],
            2,
            [4000, 5000],
        ),
    ]
)
async def test_get_transactions__with_all_filters(
    db_session: AsyncSession,
    categories_names: list[str],
    create_user: bool,
    amounts: list[int],
    descriptions: list[str],
    datetimes: list[datetime],
    min_amount: int,
    max_amount: int,
    search_term: str,
    datetime_from: datetime,
    datetime_to: datetime,
    sort_params: list[SortParam],
    expected_spendings_qty: int,
    expected_amounts: list[int],
) -> None:
    mock_user_username = "TONALI"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    categories_ids = []
    for category_name in categories_names:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )
        categories_ids.append(category.id)

    for i in range(len(amounts)):
        transaction_to_create = STransactionCreateInDB(
            amount=amounts[i],
            description=descriptions[i],
            date=datetimes[i],
            user_id=user.id,
            category_id=categories_ids[i % len(categories_ids)],
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

    spendings = await spendings_repo.get_transactions_from_db(
        user_id=user.id,
        categories_ids=categories_ids,
        min_amount=min_amount,
        max_amount=max_amount,
        description_search_term=search_term,
        datetime_from=datetime_from,
        datetime_to=datetime_to,
        sort_params=sort_params,
        session=db_session,
    )
    assert len(spendings) == expected_spendings_qty
    for spending in spendings:
        assert spending.amount in expected_amounts
