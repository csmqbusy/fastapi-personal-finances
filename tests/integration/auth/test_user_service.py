from contextlib import nullcontext
from typing import ContextManager

import pytest
from factory.faker import faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.user_exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
)
from app.models import UserModel
from app.schemas.user_schemas import SUserSignUp
from app.services.user_service import (
    _check_unique_email,
    _check_unique_username,
    create_user,
    get_user_by_username,
)
from tests.factories import UserFactory

fake = faker.Faker()


@pytest.mark.asyncio
async def test__check_unique_username(
    db_session: AsyncSession,
    user: UserModel,
):
    assert await _check_unique_username(user.username, db_session) is False


@pytest.mark.asyncio
async def test__check_unique_email(
    db_session: AsyncSession,
    user: UserModel,
):
    assert await _check_unique_email(user.email, db_session) is False


@pytest.mark.asyncio
async def test_get_user_by_username(
    db_session: AsyncSession,
    user: UserModel,
):
    user_from_db = await get_user_by_username(user.username, db_session)
    assert isinstance(user_from_db, UserModel)
    assert user_from_db.id == user.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "add_with_same_username, add_with_same_email, expectation",
    [
        (False, False, nullcontext()),
        (True, False, pytest.raises(UsernameAlreadyExists)),
        (False, True, pytest.raises(EmailAlreadyExists)),
    ]
)
async def test_add_user(
    db_session: AsyncSession,
    add_with_same_username: True,
    add_with_same_email: True,
    expectation: ContextManager,
):
    user = UserFactory()
    user_schema = SUserSignUp.model_validate(user)
    with expectation:
        await create_user(user_schema, db_session)
        user_from_db = await get_user_by_username(user.username, db_session)
        assert isinstance(user_from_db, UserModel)
        assert user_from_db.username == user.username
        assert user_from_db.email == user.email

        if add_with_same_username:
            user_schema.email = fake.email()
            await create_user(user_schema, db_session)
        if add_with_same_email:
            user_schema.username = fake.user_name()
            await create_user(user_schema, db_session)
