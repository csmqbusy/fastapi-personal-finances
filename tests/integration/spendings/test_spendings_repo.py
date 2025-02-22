from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UsersSpendingCategoriesModel
from app.repositories import spendings_repo, user_repo
from app.schemas.transactions_schemas import STransactionCreateInDB, SortParam
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
    "category_name, create_user, prices, sorted_prices",
    [
        (
            "Food",
            True,
            [200, 500, 400, 100, 300],
            [100, 200, 300, 400, 500],
        ),
    ]
)
async def test_get_transactions__with_sort(
    db_session: AsyncSession,
    category_name: str,
    create_user: bool,
    prices: list[int],
    sorted_prices: list[int],
) -> None:
    mock_user_username = "THURAM"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    category = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_name,
        db_session,
    )

    for p in prices:
        transaction_to_create = STransactionCreateInDB(
            amount=p,
            description="Some description",
            date=None,
            user_id=user.id,
            category_id=category.id,
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

    spendings = await spendings_repo.get_transactions(
        session=db_session,
        query_params=dict(user_id=user.id, category_id=category.id),
    )
    assert [s.amount for s in spendings] == prices

    spendings = await spendings_repo.get_transactions(
        session=db_session,
        query_params=dict(user_id=user.id, category_id=category.id),
        sort_params=[SortParam(order_by="amount", order_direction="asc")]
    )
    assert len(spendings) == len(prices)
    assert [s.amount for s in spendings] == sorted_prices


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "category_name",
        "create_user",
        "datetimes",
        "datetime_from",
        "datetime_to",
        "expected_spendings_qty",
    ),
    [
        (
            "Food",
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
    category_name: str,
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

    category = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_name,
        db_session,
    )

    for dt in datetimes:
        transaction_to_create = STransactionCreateInDB(
            amount=999,
            description="Some description",
            date=dt,
            user_id=user.id,
            category_id=category.id,
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

    spendings = await spendings_repo.get_transactions(
        session=db_session,
        query_params=dict(user_id=user.id, category_id=category.id),
    )
    assert [s.date for s in spendings] == datetimes

    spendings = await spendings_repo.get_transactions(
        session=db_session,
        query_params=dict(user_id=user.id, category_id=category.id),
        datetime_from=datetime_from,
        datetime_to=datetime_to,
    )
    assert len(spendings) == expected_spendings_qty
    for sp in spendings:
        assert sp.date >= datetime_from
        assert sp.date <= datetime_to
