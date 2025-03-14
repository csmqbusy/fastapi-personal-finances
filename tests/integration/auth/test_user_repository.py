import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserModel
from app.repositories import user_repo
from tests.factories import UserFactory
from tests.helpers import add_obj_to_db, create_batch


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "add_duplicate",
    [False, True],
)
async def test_add_user(
    db_session: AsyncSession,
    user: UserModel,
    add_duplicate: bool,
):
    assert user
    if add_duplicate:
        users_before = await user_repo.get_all(db_session)
        await add_obj_to_db(user, db_session)
        users_after = await user_repo.get_all(db_session)
        assert len(users_before) == len(users_after)


@pytest.mark.asyncio
async def test_get_user(
    db_session: AsyncSession,
    user: UserModel,
):
    user_from_db = await user_repo.get(db_session, user.id)
    assert user_from_db.id == user.id


@pytest.mark.asyncio
async def test_get_all_users(db_session: AsyncSession):
    num_of_users = 10
    users_before = await user_repo.get_all(db_session)
    await create_batch(UserFactory, num_of_users, db_session)
    users_after = await user_repo.get_all(db_session)
    assert len(users_before) == len(users_after) - num_of_users


@pytest.mark.asyncio
async def test_get_user_by_filter(
    db_session: AsyncSession,
    user: UserModel,
):
    user_from_db = await user_repo.get_one_by_filter(
        db_session,
        {"email": user.email, "username": user.username},
    )
    assert user_from_db.username == user.username
    assert user_from_db.email == user.email


@pytest.mark.asyncio
async def test_delete_user(
    db_session: AsyncSession,
    user: UserModel,
):
    users_before = await user_repo.get_all(db_session, {})
    assert await user_repo.get(db_session, user.id)

    await user_repo.delete(db_session, user.id)
    assert (await user_repo.get(db_session, user.id)) is None

    users_after = await user_repo.get_all(db_session, {})
    assert len(users_before) == len(users_after) + 1
