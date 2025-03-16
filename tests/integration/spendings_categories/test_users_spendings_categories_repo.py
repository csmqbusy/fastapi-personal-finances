import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel
from app.repositories import user_spend_cat_repo
from tests.factories import UsersSpendingCategoriesFactory
from tests.helpers import add_obj_to_db


@pytest.mark.asyncio
async def test_add_category__success(
    db_session: AsyncSession,
    user: UserModel,
):
    category_name = "Food"
    category = await user_spend_cat_repo.add(
        db_session,
        dict(user_id=user.id, category_name=category_name),
    )
    assert category.category_name == category_name

    categories = await user_spend_cat_repo.get_all(
        db_session,
        dict(user_id=user.id),
    )
    assert len(categories) == 1


@pytest.mark.asyncio
async def test_add_category__error(
    db_session: AsyncSession,
    user: UserModel,
):
    with pytest.raises(IntegrityError):
        for _ in range(2):
            await user_spend_cat_repo.add(
                db_session,
                dict(user_id=user.id, category_name="Food"),
            )


@pytest.mark.asyncio
async def test_get_category(
    db_session: AsyncSession,
    user: UserModel,
):
    category = UsersSpendingCategoriesFactory(user_id=user.id)
    await add_obj_to_db(category, db_session)
    category_from_db = await user_spend_cat_repo.get_category(
        db_session,
        user.id,
        category.category_name,
    )
    assert category.id == category_from_db.id
