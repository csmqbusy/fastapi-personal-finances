from contextlib import nullcontext
from typing import ContextManager

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_spend_cat_repo, user_repo
from tests.integration.spendings_categories.helpers import add_mock_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, curr_num_of_categories, expectation, create_user,",
    [
        (
            "Food",
            1,
            nullcontext(),
            True,
        ),
        (
            "Food",
            1,
            pytest.raises(IntegrityError),
            False,
        ),
        (
            "Health",
            2,
            nullcontext(),
            False,
        ),
    ]
)
async def test_add_category(
    db_session: AsyncSession,
    category_name: str,
    curr_num_of_categories: int,
    expectation: ContextManager,
    create_user: bool,
):
    mock_user_username = "MESSI10"
    if create_user:
        await add_mock_user(db_session, mock_user_username)

    user = await user_repo.get_by_username(db_session, mock_user_username)

    with expectation:
        await user_spend_cat_repo.add(
            db_session,
            dict(user_id=user.id, category_name=category_name),
        )

        category = await user_spend_cat_repo.get_category(
            db_session,
            user.id,
            category_name,
        )
        assert category.category_name == category_name

        categories = await user_spend_cat_repo.get_all(
            db_session,
            dict(user_id=user.id),
        )
        assert len(categories) == curr_num_of_categories


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, create_user,",
    [
        (
            "Food2",
            True,
        ),
        (
            "Food",
            False,
        ),
        (
            "foo",
            False,
        )
    ]
)
async def test_get_category(
    db_session: AsyncSession,
    category_name: str,
    create_user: bool,
):
    mock_user_username = "RONALDO7"
    if create_user:
        await add_mock_user(db_session, mock_user_username)

    user = await user_repo.get_by_username(db_session, mock_user_username)

    category = await user_spend_cat_repo.get_category(
        db_session,
        user.id,
        category_name,
    )
    assert category is None

    await user_spend_cat_repo.add(
        db_session,
        dict(user_id=user.id, category_name=category_name),
    )

    category = await user_spend_cat_repo.get_category(
        db_session,
        user.id,
        category_name,
    )
    assert category.category_name == category_name
    assert category.user_id == user.id

