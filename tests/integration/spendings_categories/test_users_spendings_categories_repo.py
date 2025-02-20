from contextlib import nullcontext
from typing import ContextManager
from random import randint

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_spend_cat_repo, user_repo
from app.schemas.user_schemas import SUserSignUp


async def _add_mock_user(db_session: AsyncSession, username: str) -> None:
    mock_email = f"mock{randint(1, 100_000_000)}{randint(1, 100_000_000)}@i.ai"
    user_schema = SUserSignUp(
        username=username,
        password=b"qwerty",
        email=mock_email,  # type: ignore
    )
    await user_repo.add(db_session, user_schema.model_dump())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, curr_num_of_categories, expectation, add_user,",
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
    add_user: bool,
):
    mock_user_username = "MESSI"
    if add_user:
        await _add_mock_user(db_session, mock_user_username)

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
