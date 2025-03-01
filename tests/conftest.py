from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.dependencies import database_manager
from app.main import main_app
from app.models import Base


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
