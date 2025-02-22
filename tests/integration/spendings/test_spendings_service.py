from contextlib import nullcontext
from datetime import datetime
from typing import ContextManager

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.categories_exceptions import CategoryNotFound
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.repositories import user_repo
from app.schemas.transactions_schemas import (
    STransactionCreate,
    STransactionResponse, STransactionUpdatePartial,
)
from app.services import user_spend_cat_service, spendings_service
from tests.integration.helpers import add_mock_user


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
        "expectation_for_get"),
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
