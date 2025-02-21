from contextlib import nullcontext
from typing import ContextManager

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.categories_exceptions import (
    CategoryAlreadyExists,
    CategoryNotFound,
    CannotDeleteDefaultCategory,
)
from app.repositories import user_repo, spendings_repo
from app.schemas.transaction_category_schemas import (
    STransactionCategoryCreate,
    STransactionCategoryUpdate,
    TransactionsOnDeleteActions,
)
from app.schemas.transactions_schemas import STransactionCreateInDB
from app.services import user_spend_cat_service
from tests.conftest import db_session
from tests.integration.spendings_categories.helpers import (
    add_mock_user,
    create_spendings,
)


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, transactions_actions, expectation, create_user",
    [
        (
            settings.app.default_spending_category_name,
            TransactionsOnDeleteActions.DELETE,
            pytest.raises(CannotDeleteDefaultCategory),
            True,
        ),
        (
            settings.app.default_spending_category_name.upper(),
            TransactionsOnDeleteActions.DELETE,
            pytest.raises(CannotDeleteDefaultCategory),
            False,
        ),
    ]
)
async def test_delete_category__delete_default_category(
    db_session: AsyncSession,
    category_name: str,
    transactions_actions: TransactionsOnDeleteActions,
    expectation: ContextManager,
    create_user: bool,
):
    mock_user_username = "MAKELELE"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    if create_user:
        await user_spend_cat_service.add_user_default_category(
            user.id,
            db_session,
        )

    with expectation:
        await user_spend_cat_service.delete_category(
            category_name=category_name,
            user_id=user.id,
            transactions_actions=transactions_actions,
            new_category_name=None,
            session=db_session,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, transactions_actions, expectation, create_user",
    [
        (
            "Games",
            TransactionsOnDeleteActions.DELETE,
            pytest.raises(CategoryNotFound),
            True,
        ),
    ]
)
async def test_delete_category__delete_unknown_category(
    db_session: AsyncSession,
    category_name: str,
    transactions_actions: TransactionsOnDeleteActions,
    expectation: ContextManager,
    create_user: bool,
):
    mock_user_username = "ONANA"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    with expectation:
        await user_spend_cat_service.delete_category(
            category_name=category_name,
            user_id=user.id,
            transactions_actions=transactions_actions,
            new_category_name=None,
            session=db_session,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, num_of_spendings, transactions_action, create_user",
    [
        (
            "Games",
            10,
            TransactionsOnDeleteActions.DELETE,
            True,
        ),
    ]
)
async def test_delete_category__delete_spendings_with_category(
    db_session: AsyncSession,
    category_name: str,
    num_of_spendings: int,
    transactions_action: TransactionsOnDeleteActions,
    create_user: bool,
):
    mock_user_username = "SON"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    if create_user:
        await user_spend_cat_service.add_user_default_category(
            user.id,
            db_session,
        )

    category_schema = STransactionCategoryCreate(category_name=category_name)
    category = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_schema.category_name,
        db_session,
    )

    await create_spendings(num_of_spendings, user.id, None, db_session)

    # add transactions
    await create_spendings(num_of_spendings, user.id, category.id, db_session)
    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    all_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id)
    )
    assert len(category_transactions) == num_of_spendings
    assert len(all_transactions) == num_of_spendings * 2

    await user_spend_cat_service.delete_category(
        category_name=category_name,
        user_id=user.id,
        transactions_actions=transactions_action,
        new_category_name=None,
        session=db_session,
    )

    transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(transactions) == 0

    all_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id)
    )
    assert len(all_transactions) == num_of_spendings


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, num_of_spendings, transactions_action, create_user",
    [
        (
            "Games",
            50,
            TransactionsOnDeleteActions.TO_DEFAULT,
            True,
        ),
    ]
)
async def test_delete_category__move_spendings_to_default_category(
    db_session: AsyncSession,
    category_name: str,
    num_of_spendings: int,
    transactions_action: TransactionsOnDeleteActions,
    create_user: bool,
):
    mock_user_username = "HENRY"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    if create_user:
        await user_spend_cat_service.add_user_default_category(
            user.id,
            db_session,
        )

    category_schema = STransactionCategoryCreate(category_name=category_name)
    category = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_schema.category_name,
        db_session,
    )

    await create_spendings(num_of_spendings, user.id, None, db_session)
    await create_spendings(num_of_spendings, user.id, category.id, db_session)

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    all_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id)
    )
    assert len(category_transactions) == num_of_spendings
    assert len(all_transactions) == num_of_spendings * 2

    await user_spend_cat_service.delete_category(
        category_name=category_name,
        user_id=user.id,
        transactions_actions=transactions_action,
        new_category_name=None,
        session=db_session,
    )

    transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(transactions) == 0

    all_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id)
    )
    assert len(all_transactions) == num_of_spendings * 2

    default_category = await user_spend_cat_service.get_default_category(
            user.id,
            db_session,
        )
    default_category_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id, category_id=default_category.id)
    )
    assert len(default_category_transactions) == num_of_spendings * 2
