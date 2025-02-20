from contextlib import nullcontext
from typing import ContextManager

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.categories_exceptions import CategoryAlreadyExists
from app.repositories import user_repo
from app.services import user_spend_cat_service
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

    with expectation:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            category_name,
            db_session,
        )
        assert type(category) is user_spend_cat_service.out_schema
        assert category.category_name == category_name
        assert category.user_id == user.id
