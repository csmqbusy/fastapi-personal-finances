from contextlib import nullcontext
from typing import ContextManager

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.categories_exceptions import (
    CannotDeleteDefaultCategory,
    CategoryAlreadyExists,
    CategoryNameNotFound,
    CategoryNotFound,
)
from app.models import UserModel
from app.repositories import spendings_repo
from app.schemas.transaction_category_schemas import (
    STransactionCategoryCreate,
    STransactionCategoryUpdate,
    TransactionsOnDeleteActions,
)
from app.services import user_spend_cat_service
from tests.factories import SpendingsFactory, UsersSpendingCategoriesFactory
from tests.helpers import (
    add_default_spendings_category,
    add_obj_to_db,
    create_batch,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, expectation",
    [
        ("Food", nullcontext()),
        ("c@t ***", nullcontext()),
    ]
)
async def test_add_category_to_db__success(
    db_session: AsyncSession,
    user: UserModel,
    category_name: str,
    expectation: ContextManager,
):
    category_schema = STransactionCategoryCreate(category_name=category_name)
    with expectation:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_schema.category_name,
            db_session,
        )
        assert category.category_name == category_schema.category_name
        assert category.user_id == user.id


@pytest.mark.asyncio
async def test_add_category_to_db__error(
    db_session: AsyncSession,
    user: UserModel,
):
    with pytest.raises(CategoryAlreadyExists):
        for _ in range(2):
            await user_spend_cat_service.add_category_to_db(
                user.id,
                "category_name",
                db_session,
            )


@pytest.mark.asyncio
async def test_get_category(db_session: AsyncSession, user: UserModel):
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)
    category_from_db = await user_spend_cat_service.get_category(
        user.id,
        category.category_name,
        db_session,
    )
    assert category_from_db.category_name == category.category_name
    assert category_from_db.user_id == user.id


@pytest.mark.asyncio
async def test_create_and_get_default_category(
    db_session: AsyncSession,
    user: UserModel,
):
    with pytest.raises(CategoryNotFound):
        await user_spend_cat_service.get_default_category(user.id, db_session)

    await user_spend_cat_service.add_user_default_category(user.id, db_session)
    category = await user_spend_cat_service.get_default_category(
        user.id,
        db_session,
    )
    assert category.category_name == user_spend_cat_service.default_category_name
    assert category.user_id == user.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "num_of_categories",
    [1, 100, 0, 9]
)
async def test_get_user_categories(
    db_session: AsyncSession,
    user: UserModel,
    num_of_categories: int,
):
    await create_batch(
        db_session,
        num_of_categories,
        UsersSpendingCategoriesFactory,
        dict(user_id=user.id),
    )
    categories = await user_spend_cat_service.get_user_categories(
        user.id,
        db_session,
    )
    assert len(categories) == num_of_categories


@pytest.mark.asyncio
async def test_update_category__success(
    db_session: AsyncSession,
    user: UserModel,
    category_update_obj: STransactionCategoryUpdate,
):
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)
    category_from_db = await user_spend_cat_service.update_category(
        category.category_name,
        user.id,
        category_update_obj,
        db_session,
    )
    assert category_from_db.id == category.id
    assert category_from_db.category_name == category_update_obj.category_name
    assert category_from_db.user_id == user.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, new_category_name, create_category, expectation",
    [
        ("Food", "FOOD ", True, pytest.raises(CategoryAlreadyExists)),
        ("Cat food", "Pet food", False, pytest.raises(CategoryNotFound)),
    ]
)
async def test_update_category__error(
    db_session: AsyncSession,
    user: UserModel,
    category_name: str,
    new_category_name: str,
    create_category: bool,
    expectation: ContextManager,
):
    if create_category:
        category = UsersSpendingCategoriesFactory(
            user_id=user.id, category_name=category_name
        )
        await add_obj_to_db(category, db_session)

    with expectation:
        category_update_obj = STransactionCategoryUpdate(
            category_name=new_category_name,
        )
        await user_spend_cat_service.update_category(
            category_name,
            user.id,
            category_update_obj,
            db_session,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "num_of_transactions",
    [10, 0]
)
async def test__change_transactions_category(
    db_session: AsyncSession,
    user: UserModel,
    num_of_transactions: int,
):
    original_category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(original_category, db_session)

    changed_category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(changed_category, db_session)

    for i in range(num_of_transactions):
        spending = SpendingsFactory(user_id=user.id, category_id=original_category.id)
        await add_obj_to_db(spending, db_session)

    transactions = await spendings_repo.get_all(
        db_session, dict(category_id=original_category.id, user_id=user.id)
    )
    assert len(transactions) == num_of_transactions

    await user_spend_cat_service._change_transactions_category(
        transactions,
        changed_category.id,
        db_session,
    )

    transactions_with_original_category = await spendings_repo.get_all(
        db_session, dict(category_id=original_category.id, user_id=user.id)
    )
    assert len(transactions_with_original_category) == 0

    transactions_with_changed_category = await spendings_repo.get_all(
        db_session, dict(category_id=changed_category.id, user_id=user.id)
    )
    assert len(transactions_with_changed_category) == num_of_transactions


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name",
    [
        settings.app.default_spending_category_name,
        settings.app.default_spending_category_name.upper(),
    ]
)
async def test_delete_category__delete_default_category(
    db_session: AsyncSession,
    user: UserModel,
    category_name: str,
):
    with pytest.raises(CannotDeleteDefaultCategory):
        await user_spend_cat_service.delete_category(
            category_name=category_name,
            user_id=user.id,
            transactions_actions=TransactionsOnDeleteActions.DELETE,
            new_category_name=None,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_delete_category__delete_unknown_category(
    db_session: AsyncSession,
    user: UserModel,
):
    category_name = "Games"
    with pytest.raises(CategoryNotFound):
        await user_spend_cat_service.delete_category(
            category_name=category_name,
            user_id=user.id,
            transactions_actions=TransactionsOnDeleteActions.DELETE,
            new_category_name=None,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_delete_category__delete_spendings_with_category(
    db_session: AsyncSession,
    user: UserModel,
):
    num_of_spendings = 10
    default_cat = await add_default_spendings_category(user.id, db_session)

    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)

    await create_batch(
        db_session,
        num_of_spendings,
        SpendingsFactory,
        dict(user_id=user.id, category_id=default_cat.id),
    )
    await create_batch(
        db_session,
        num_of_spendings,
        SpendingsFactory,
        dict(user_id=user.id, category_id=category.id),
    )

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    all_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id)
    )
    assert len(category_transactions) == num_of_spendings
    assert len(all_transactions) == num_of_spendings * 2

    await user_spend_cat_service.delete_category(
        category_name=category.category_name,
        user_id=user.id,
        transactions_actions=TransactionsOnDeleteActions.DELETE,
        new_category_name=None,
        session=db_session,
    )

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(category_transactions) == 0

    all_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id)
    )
    assert len(all_transactions) == num_of_spendings


@pytest.mark.asyncio
async def test_delete_category__move_spendings_to_default_category(
    db_session: AsyncSession,
    user: UserModel,
):
    num_of_spendings = 10
    default_cat = await add_default_spendings_category(user.id, db_session)

    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)

    await create_batch(
        db_session,
        num_of_spendings,
        SpendingsFactory,
        dict(user_id=user.id, category_id=default_cat.id),
    )
    await create_batch(
        db_session,
        num_of_spendings,
        SpendingsFactory,
        dict(user_id=user.id, category_id=category.id),
    )

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(category_transactions) == num_of_spendings

    default_category_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id, category_id=default_cat.id)
    )
    assert len(default_category_transactions) == num_of_spendings

    await user_spend_cat_service.delete_category(
        category_name=category.category_name,
        user_id=user.id,
        transactions_actions=TransactionsOnDeleteActions.TO_DEFAULT,
        new_category_name=None,
        session=db_session,
    )

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(category_transactions) == 0

    default_category_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id, category_id=default_cat.id)
    )
    assert len(default_category_transactions) == num_of_spendings * 2


@pytest.mark.asyncio
async def test_delete_category__move_spendings_to_new_category__success(
    db_session: AsyncSession,
    user: UserModel,
):
    num_of_spendings = 20
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)
    new_category_name = "mock_name"

    await create_batch(
        db_session,
        num_of_spendings,
        SpendingsFactory,
        dict(user_id=user.id, category_id=category.id),
    )

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(category_transactions) == num_of_spendings

    await user_spend_cat_service.delete_category(
        category_name=category.category_name,
        user_id=user.id,
        transactions_actions=TransactionsOnDeleteActions.TO_NEW_CAT,
        new_category_name=new_category_name,
        session=db_session,
    )

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(category_transactions) == 0

    new_category = await user_spend_cat_service.get_category(
        user_id=user.id,
        category_name=new_category_name,
        session=db_session,
    )
    new_category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=new_category.id, user_id=user.id)
    )
    assert len(new_category_transactions) == num_of_spendings


@pytest.mark.asyncio
async def test_delete_category__move_spendings_to_new_category__error(
    db_session: AsyncSession,
    user: UserModel,
):
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)
    with pytest.raises(CategoryNameNotFound):
        await user_spend_cat_service.delete_category(
            category_name=category.category_name,
            user_id=user.id,
            transactions_actions=TransactionsOnDeleteActions.TO_NEW_CAT,
            new_category_name=None,
            session=db_session,
        )


@pytest.mark.asyncio
async def test_delete_category__move_spendings_to_exists_category__success(
    db_session: AsyncSession,
    user: UserModel,
):
    num_of_spendings = 20
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)
    exists_category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(exists_category, db_session)

    await create_batch(
        db_session,
        num_of_spendings,
        SpendingsFactory,
        dict(user_id=user.id, category_id=category.id),
    )

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(category_transactions) == num_of_spendings

    await user_spend_cat_service.delete_category(
        category_name=category.category_name,
        user_id=user.id,
        transactions_actions=TransactionsOnDeleteActions.TO_EXISTS_CAT,
        new_category_name=exists_category.category_name,
        session=db_session,
    )

    category_transactions = await spendings_repo.get_all(
        db_session, dict(category_id=category.id, user_id=user.id)
    )
    assert len(category_transactions) == 0

    exists_category_transactions = await spendings_repo.get_all(
        db_session, dict(user_id=user.id, category_id=exists_category.id)
    )
    assert len(exists_category_transactions) == num_of_spendings


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pass_wrong_exists_category_name, expectation",
    [
        (False, pytest.raises(CategoryNotFound)),
        (True, pytest.raises(CategoryNameNotFound)),
    ]
)
async def test_delete_category__move_spendings_to_exists_category__error(
    db_session: AsyncSession,
    user: UserModel,
    pass_wrong_exists_category_name: bool,
    expectation: ContextManager,
):
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)
    exists_category = UsersSpendingCategoriesFactory(user_id=user.id)
    exists_category_name = exists_category.category_name
    if pass_wrong_exists_category_name:
        exists_category_name = None

    with expectation:
        await user_spend_cat_service.delete_category(
            category_name=category.category_name,
            user_id=user.id,
            transactions_actions=TransactionsOnDeleteActions.TO_EXISTS_CAT,
            new_category_name=exists_category_name,
            session=db_session,
        )
