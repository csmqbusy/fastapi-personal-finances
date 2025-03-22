from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.dependencies import database_manager
from app.main import main_app
from app.models import Base, UserModel
from app.schemas.saving_goals_schemas import SSavingGoalUpdatePartial
from app.services import user_spend_cat_service
from tests.factories import (
    SavingGoalUpdateFactory,
    TransactionCategoryUpdateFactory,
    UserFactory,
)
from tests.helpers import add_obj_to_db


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    assert settings.mode == "TEST"

    async with database_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with database_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
@pytest.fixture(scope="function")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=main_app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in database_manager.get_session():
        yield session


@pytest.fixture
async def user(db_session: AsyncSession) -> UserModel:
    user = await add_obj_to_db(UserFactory(), db_session)
    return user


@pytest.fixture
async def auth_user(
    db_session: AsyncSession,
    client: AsyncClient,
    user: UserModel
) -> UserModel:
    await user_spend_cat_service.add_user_default_category(user.id, db_session)
    await client.post(
        url=f"{settings.api.prefix_v1}/sign_in/",
        data={
            "username": user.username,
            "password": "password",
        }
    )
    return user


@pytest.fixture
async def saving_goal_update_obj() -> SSavingGoalUpdatePartial:
    return SavingGoalUpdateFactory()


@pytest.fixture
async def category_update_obj() -> TransactionCategoryUpdateFactory:
    return TransactionCategoryUpdateFactory()
