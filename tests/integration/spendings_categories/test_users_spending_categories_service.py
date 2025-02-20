from contextlib import nullcontext
from typing import ContextManager

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.categories_exceptions import (
    CategoryAlreadyExists,
    CategoryNotFound,
)
from app.repositories import user_repo, spendings_repo
from app.schemas.transaction_category_schemas import (
    STransactionCategoryCreate,
    STransactionCategoryUpdate,
)
from app.schemas.transactions_schemas import STransactionCreateInDB
from app.services import user_spend_cat_service
from tests.conftest import db_session
from tests.integration.spendings_categories.helpers import add_mock_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, expectation, create_user",
    [
        (
            "Food",
            nullcontext(),
            True,
        ),
        (
            "food",
            pytest.raises(CategoryAlreadyExists),
            False,
        ),
        (
            "c@t ***",
            nullcontext(),
            False,
        ),
    ]
)
async def test_add_category_to_db(
    db_session: AsyncSession,
    category_name: str,
    expectation: ContextManager,
    create_user: bool,
):
    mock_user_username = "AGUERO"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    category_schema = STransactionCategoryCreate(category_name=category_name)
    with expectation:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_schema.category_name,
            db_session,
        )
        assert type(category) is user_spend_cat_service.out_schema
        assert category.category_name == category_schema.category_name
        assert category.user_id == user.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, expectation, create_user",
    [
        (
            "Food",
            nullcontext(),
            True,
        ),
        (
            "  food ",
            pytest.raises(CategoryAlreadyExists),
            False,
        ),
        (
            "c@t ***",
            nullcontext(),
            False,
        ),
    ]
)
async def test_get_category(
    db_session: AsyncSession,
    category_name: str,
    expectation: ContextManager,
    create_user: bool,
):
    mock_user_username = "DI_MARIA"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    category_schema = STransactionCategoryCreate(category_name=category_name)
    with expectation:
        await user_spend_cat_service.add_category_to_db(
            user.id,
            category_schema.category_name,
            db_session,
        )
        category = await user_spend_cat_service.get_category(
            user.id,
            category_schema.category_name,
            db_session,
        )
        assert category.category_name == category_schema.category_name
        assert category.user_id == user.id


async def test_create_and_get_default_category(db_session: AsyncSession):
    mock_user_username = "RAPHINHA"
    await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    category = await user_spend_cat_service.get_default_category(
        user.id,
        db_session,
    )
    assert category is None

    await user_spend_cat_service.add_user_default_category(user.id, db_session)
    category = await user_spend_cat_service.get_default_category(
        user.id,
        db_session,
    )
    assert category is not None
    assert category.category_name == user_spend_cat_service.default_category_name
    assert category.user_id == user.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mock_user_username, num_of_categories",
    [
        (
            "FORLAN1",
            1,
        ),
        (
            "FORLAN2",
            100,
        ),
        (
            "FORLAN3",
            0,
        ),
        (
            "FORLAN4",
            9,
        ),
    ]
)
async def test_get_user_categories(
    db_session: AsyncSession,
    mock_user_username,
    num_of_categories: int,
):
    await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    for i in range(num_of_categories):
        category_schema = STransactionCategoryCreate(
            category_name=f"Category {i}",
        )
        await user_spend_cat_service.add_category_to_db(
            user.id,
            category_schema.category_name,
            db_session,
        )

    categories = await user_spend_cat_service.get_user_categories(
        user.id,
        db_session,
    )
    assert len(categories) == num_of_categories


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, new_category_name, create_category, expectation, create_user",
    [
        (
            "Food",
            "Luxury food ",
            True,
            nullcontext(),
            True,
        ),
        (
            "Food",
            "FOOD ",
            True,
            pytest.raises(CategoryAlreadyExists),
            False,
        ),
        (
            "Cat food",
            "Pet food",
            False,
            pytest.raises(CategoryNotFound),
            False,
        ),
    ]
)
async def test_update_category(
    db_session: AsyncSession,
    category_name: str,
    new_category_name: str,
    create_category: bool,
    expectation: ContextManager,
    create_user: bool,
):
    mock_user_username = "RODRI"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    old_category = None
    if create_category:
        category_schema = STransactionCategoryCreate(
            category_name=category_name,
        )
        old_category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_schema.category_name,
            db_session,
        )

    with expectation:
        category_update_obj = STransactionCategoryUpdate(
            category_name=new_category_name,
        )
        category = await user_spend_cat_service.update_category(
            category_name,
            user.id,
            category_update_obj,
            db_session,
        )

        assert category.category_name == category_update_obj.category_name
        assert category.user_id == user.id
        if old_category:
            assert category.id == old_category.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "original_category, changed_category, num_of_transactions, create_user",
    [
        (
            "Food",
            "Luxury food",
            10,
            True,
        ),
        (
            "Health",
            "Mental Health",
            0,
            False,
        ),
    ]
)
async def test__change_transactions_category(
    db_session: AsyncSession,
    original_category: str,
    changed_category: str,
    num_of_transactions: int,
    create_user: bool,
):
    mock_user_username = "BOJAN"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    # add original category
    category_schema = STransactionCategoryCreate(
        category_name=original_category,
    )
    original_category = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_schema.category_name,
        db_session,
    )

    # add transactions
    for i in range(num_of_transactions):
        transaction_to_create = STransactionCreateInDB(
            amount=1000 + i,
            description=None,
            date=None,
            user_id=user.id,
            category_id=original_category.id,
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )

    # add changed category
    category_schema = STransactionCategoryCreate(
        category_name=changed_category,
    )
    changed_category_from_db = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_schema.category_name,
        db_session,
    )
    new_category_id = changed_category_from_db.id

    transactions = await spendings_repo.get_all(
        db_session, dict(category_id=original_category.id, user_id=user.id)
    )

    assert len(transactions) == num_of_transactions

    await user_spend_cat_service._change_transactions_category(
        transactions,
        new_category_id,
        db_session,
    )

    transactions_with_original_category = await spendings_repo.get_all(
        db_session, dict(category_id=original_category.id, user_id=user.id)
    )
    assert len(transactions_with_original_category) == 0

    transactions_with_changed_category = await spendings_repo.get_all(
        db_session, dict(category_id=new_category_id, user_id=user.id)
    )
    assert len(transactions_with_changed_category) == num_of_transactions
