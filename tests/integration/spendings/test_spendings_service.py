from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
    "create_user, amount, description, date, new_category_name",
    [
        (
            True,
            8000,
            "New description",
            datetime(year=2020, month=12, day=31, hour=23, minute=0, second=0),
            "New category",
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

    await spendings_service.update_transaction(
        spending.id,
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
