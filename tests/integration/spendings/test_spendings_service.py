from contextlib import nullcontext
from datetime import datetime
from typing import ContextManager

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.categories_exceptions import CategoryNotFound
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.repositories import user_repo, spendings_repo
from app.schemas.date_range_schemas import SDatetimeRange
from app.schemas.transactions_schemas import (
    STransactionCreate,
    STransactionResponse,
    STransactionUpdatePartial,
    STransactionCreateInDB,
    STransactionsSortParams,
    SortParam,
    SAmountRange,
)
from app.schemas.transaction_category_schemas import SCategoryQueryParams
from app.services import user_spend_cat_service, spendings_service
from tests.integration.helpers import add_mock_user, create_spendings


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, create_user",
    [
        (
            "Food",
            True,
        ),
        (
            None,
            False,
        ),
    ]
)
async def test_add_transaction_to_db(
    db_session: AsyncSession,
    category_name: str | None,
    create_user: bool,
):
    mock_user_username = "YAMAL"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    if create_user:
        await user_spend_cat_service.add_user_default_category(
            user.id,
            db_session,
        )

    if category_name:
        await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )

    spending_schema = STransactionCreate(
        amount=100,
        category_name=category_name,
    )
    spending = await spendings_service.add_transaction_to_db(
        spending_schema,
        user.id,
        db_session,
    )
    assert spending is not None
    assert type(spending) is STransactionResponse
    if category_name:
        assert spending.category_name == category_name
    else:
        assert spending.category_name == settings.app.default_spending_category_name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "create_user",
        "amount",
        "description",
        "date",
        "new_category_name",
        "create_category",
        "wrong_spending_id",
        "expectation",
    ),
    [
        (
            True,
            8000,
            "New description",
            datetime(year=2020, month=12, day=31, hour=23, minute=0, second=0),
            "New category",
            True,
            False,
            nullcontext(),
        ),
        (
            False,
            8000,
            "New description",
            datetime(year=2020, month=12, day=31, hour=23, minute=0, second=0),
            "Missing",
            False,
            False,
            pytest.raises(CategoryNotFound),
        ),
        (
            False,
            8000,
            "New description",
            datetime(year=2020, month=12, day=31, hour=23, minute=0, second=0),
            "Missing",
            True,
            True,
            pytest.raises(TransactionNotFound),
        ),
    ]
)
async def test_update_transaction(
    db_session: AsyncSession,
    create_user: bool,
    amount: int,
    description: str,
    date: datetime,
    new_category_name: str,
    create_category: bool,
    wrong_spending_id: bool,
    expectation: ContextManager,
):
    mock_user_username = "NICO"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    if create_user:
        await user_spend_cat_service.add_user_default_category(
            user.id,
            db_session,
        )
    if create_category:
        await user_spend_cat_service.add_category_to_db(
            user.id,
            new_category_name,
            db_session,
        )

    spending_schema = STransactionCreate(amount=100)
    spending = await spendings_service.add_transaction_to_db(
        spending_schema,
        user.id,
        db_session,
    )

    assert spending is not None
    assert spending.amount != amount
    assert spending.description != description
    assert spending.date != date
    assert spending.category_name != new_category_name

    spending_update = STransactionUpdatePartial(
        amount=amount,
        description=description,
        date=date,
        category_name=new_category_name,
    )

    with expectation:
        await spendings_service.update_transaction(
            spending.id + wrong_spending_id,
            user.id,
            spending_update,
            db_session,
        )

        updated_spending = await spendings_service.get_transaction(
            spending.id,
            user.id,
            db_session,
        )

        assert updated_spending is not None
        assert updated_spending.amount == amount
        assert updated_spending.description == description
        assert updated_spending.date == date
        assert updated_spending.category_name == new_category_name


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_user, wrong_spending_id, wrong_user_id, expectation",
    [
        (
            True,
            False,
            False,
            nullcontext(),
        ),
        (
            False,
            True,
            False,
            pytest.raises(TransactionNotFound),
        ),
        (
            False,
            False,
            True,
            pytest.raises(TransactionNotFound),
        ),
    ]
)
async def test_get_transaction(
    db_session: AsyncSession,
    create_user: bool,
    wrong_spending_id: bool,
    wrong_user_id: bool,
    expectation: ContextManager,
):
    mock_user_username = "INIGO"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    if create_user:
        await user_spend_cat_service.add_user_default_category(
            user.id,
            db_session,
        )

    spending_schema = STransactionCreate(amount=100)
    spending = await spendings_service.add_transaction_to_db(
        spending_schema,
        user.id,
        db_session,
    )

    with expectation:
        spending_from_db = await spendings_service.get_transaction(
            spending.id + wrong_spending_id,
            user.id + wrong_user_id,
            db_session,
        )
        assert spending_from_db is not None
        assert spending_from_db.id == spending.id
        assert spending_from_db.amount == spending.amount


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "create_user",
        "wrong_spending_id",
        "wrong_user_id",
        "expectation_for_delete",
        "expectation_for_get",
    ),
    [
        (
            True,
            False,
            False,
            nullcontext(),
            pytest.raises(TransactionNotFound),
        ),
        (
            False,
            True,
            False,
            pytest.raises(TransactionNotFound),
            nullcontext(),
        ),
        (
            False,
            False,
            True,
            pytest.raises(TransactionNotFound),
            nullcontext(),
        ),
    ]
)
async def test_delete_transaction(
    db_session: AsyncSession,
    create_user: bool,
    wrong_spending_id: bool,
    wrong_user_id: bool,
    expectation_for_delete: ContextManager,
    expectation_for_get: ContextManager,
):
    mock_user_username = "FERRAN"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    if create_user:
        await user_spend_cat_service.add_user_default_category(
            user.id,
            db_session,
        )

    spending_schema = STransactionCreate(amount=100)
    spending = await spendings_service.add_transaction_to_db(
        spending_schema,
        user.id,
        db_session,
    )

    with expectation_for_delete:
        await spendings_service.delete_transaction(
            spending.id + wrong_spending_id,
            user.id + wrong_user_id,
            db_session,
        )
        with expectation_for_get:
            await spendings_service.get_transaction(
                spending.id,
                user.id,
                db_session,
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_user, category_name, create_category, expectation",
    [
        (
            True,
            "Mock category",
            True,
            nullcontext(),
        ),
        (
            False,
            "Mock category 2",
            False,
            pytest.raises(CategoryNotFound),
        ),
    ]
)
async def test__get_category_id(
    db_session: AsyncSession,
    create_user: bool,
    category_name: str,
    create_category: bool,
    expectation: ContextManager,
):
    mock_user_username = "RETEGUI"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    category = None
    if create_category:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )

    with expectation:
        category_id = await spendings_service._get_category_id(
            user.id,
            category_name,
            db_session,
        )
        assert category.id == category_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_user, category_name, create_category, send_user_id, expectation",
    [
        (
            True,
            "Taxi",
            False,
            True,
            pytest.raises(CategoryNotFound),
        ),
    ]
)
async def test_get_transactions__errors(
    db_session: AsyncSession,
    create_user: bool,
    category_name: str,
    create_category: bool,
    send_user_id: bool,
    expectation: ContextManager,
):
    mock_user_username = "SMITHROWE"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    if create_category:
        await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )

    with expectation:
        query_params = SCategoryQueryParams(
            category_name=category_name,
        )
        await spendings_service.get_transactions(
            user_id=user.id,
            category_params=query_params,
            session=db_session,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "create_user, category_name, spendings_qty",
    [
        (
            True,
            "Candies",
            5,
        ),
    ]
)
async def test_get_transactions__category_id_priority(
    db_session: AsyncSession,
    create_user: bool,
    category_name: str,
    spendings_qty: int,
):
    mock_user_username = "OBLAK"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    cat_1 = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_name,
        db_session,
    )
    await create_spendings(
        qty=spendings_qty,
        user_id=user.id,
        category_id=cat_1.id,
        db_session=db_session,
    )

    cat_2 = await user_spend_cat_service.add_category_to_db(
        user.id,
        f"{category_name}_2",
        db_session,
    )
    await create_spendings(
        qty=spendings_qty,
        user_id=user.id,
        category_id=cat_2.id,
        db_session=db_session,
    )

    query_params = SCategoryQueryParams(
        category_id=cat_1.id,
        category_name=cat_2.category_name,
    )
    spendings = await spendings_service.get_transactions(
        user_id=user.id,
        category_params=query_params,
        session=db_session,
    )
    assert len(spendings) == spendings_qty
    spendings_category_name = [s.category_name for s in spendings]
    assert spendings_category_name == [cat_1.category_name] * spendings_qty
    assert spendings_category_name != [cat_2.category_name] * spendings_qty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "create_user",
        "category_name",
        "search_term",
        "amounts",
        "datetimes",
        "datetime_from",
        "datetime_to",
        "pass_category_name",
        "expected_spendings_qty",
    ),
    [
        (
            True,
            "Candies",
            "term",
            [100, 200, 300, 400, 500, 600, 700, 800, 900],
            [
                datetime(year=2020, month=1, day=1, hour=12),
                datetime(year=2021, month=1, day=1, hour=12),
                datetime(year=2022, month=1, day=1, hour=12),
                datetime(year=2023, month=1, day=1, hour=12),
                datetime(year=2024, month=1, day=1, hour=12),
                datetime(year=2025, month=1, day=1, hour=12),
                datetime(year=2026, month=1, day=1, hour=12),
                datetime(year=2027, month=1, day=1, hour=12),
                datetime(year=2028, month=1, day=1, hour=12),
            ],
            datetime(year=2022, month=1, day=1),
            datetime(year=2027, month=1, day=1, hour=23, minute=59, second=59),
            False,
            3,
        ),
        (
            False,
            "Alcohol",
            "vodka",
            [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000],
            [
                datetime(year=2020, month=1, day=1, hour=12),
                datetime(year=2021, month=1, day=1, hour=12),
                datetime(year=2022, month=1, day=1, hour=12),
                datetime(year=2023, month=1, day=1, hour=12),
                datetime(year=2024, month=1, day=1, hour=12),
                datetime(year=2025, month=1, day=1, hour=12),
                datetime(year=2026, month=1, day=1, hour=12),
                datetime(year=2027, month=1, day=1, hour=12),
                datetime(year=2028, month=1, day=1, hour=12),
            ],
            None,
            None,
            True,
            4,
        ),
    ]
)
async def test_get_transactions__correct(
    db_session: AsyncSession,
    create_user: bool,
    category_name: str,
    search_term: str,
    amounts: list[int],
    datetimes: list[datetime],
    datetime_from: datetime | None,
    datetime_to: datetime | None,
    pass_category_name: bool,
    expected_spendings_qty: int,
):
    mock_user_username = "GREALISH"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    category = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_name,
        db_session,
    )
    for i, dt in enumerate(datetimes):
        description = f"{i} {search_term.title()} {i}" if i % 2 else "text"
        transaction_to_create = STransactionCreateInDB(
            amount=amounts[i],
            description=description,
            date=dt,
            user_id=user.id,
            category_id=category.id,
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

    spendings = await spendings_service.get_transactions(
        user_id=user.id,
        category_params=SCategoryQueryParams(
            category_id=category.id if not pass_category_name else None,
            category_name=category_name if pass_category_name else None,
        ),
        search_term=search_term,
        datetime_range=SDatetimeRange(start=datetime_from, end=datetime_to),
        sort_params=STransactionsSortParams(
            sort_by=["id", "date", "some non existent field"],
        ),
        amount_params=SAmountRange(
            min_amount=min(amounts),
            max_amount=max(amounts),
        ),
        session=db_session,
    )
    assert len(spendings) == expected_spendings_qty
    for s in spendings:
        if datetime_from and datetime_to:
            assert datetime_from <= s.date <= datetime_to
        assert search_term.lower() in s.description.lower()


@pytest.mark.parametrize(
    "sort_params, expected_result",
    [
        (
            STransactionsSortParams(
                sort_by=[
                    "id",
                    "date",
                    "-category_name",
                ],
            ),
            [
                SortParam(order_by="id", order_direction="asc"),
                SortParam(order_by="date", order_direction="asc"),
                SortParam(order_by="category_name", order_direction="desc"),
            ],
        ),
        (
            STransactionsSortParams(
                sort_by=[
                    "-id",
                    "date",
                    "-category_name",
                    "some non existent field",
                ],
            ),
            [
                SortParam(order_by="id", order_direction="desc"),
                SortParam(order_by="date", order_direction="asc"),
                SortParam(order_by="category_name", order_direction="desc"),
            ],
        ),
        (
            STransactionsSortParams(
                sort_by=[
                    "-id_non_exist",
                    "date_non_exist",
                    "-category_name_non_exist",
                    "some_non_exist",
                ],
            ),
            None,
        ),
        (
            STransactionsSortParams(
                sort_by=[],
            ),
            None,
        ),
    ]
)
def test__parse_sort_params_for_query(
    sort_params: STransactionsSortParams,
    expected_result: list[SortParam],
):

    result = spendings_service._parse_sort_params_for_query(sort_params)
    assert result == expected_result
