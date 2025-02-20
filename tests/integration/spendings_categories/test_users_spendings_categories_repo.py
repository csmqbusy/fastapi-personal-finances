from contextlib import nullcontext
from typing import ContextManager

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_spend_cat_repo, user_repo
from app.schemas.user_schemas import SUserSignUp


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
    if add_user:
        user_schema = SUserSignUp(
            username="messi",
            password=b"qwerty",
            email="messi@example.com",  # type: ignore
        )
        await user_repo.add(db_session, user_schema.model_dump())

    user_id = (await user_repo.get_by_username(db_session, "messi")).id

    with expectation:
        await user_spend_cat_repo.add(
            db_session,
            dict(user_id=user_id, category_name=category_name),
        )

        category = await user_spend_cat_repo.get_category(
            db_session,
            user_id,
            category_name,
        )
        assert category.category_name == category_name

        categories = await user_spend_cat_repo.get_all(
            db_session,
            dict(user_id=user_id),
        )
        assert len(categories) == curr_num_of_categories
