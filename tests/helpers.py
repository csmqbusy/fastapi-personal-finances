from random import randint

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories import user_repo, spendings_repo
from app.schemas.transactions_schemas import STransactionCreateInDB
from app.schemas.user_schemas import SUserSignUp
from app.services import user_spend_cat_service


async def sign_up_user(client: AsyncClient, username: str):
    await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": username,
            "password": "password",
            "email": f"{username.lower()}@example.com",
        }
    )


async def sign_in_user(client: AsyncClient, username: str):
    await client.post(
        url=f"{settings.api.prefix_v1}/sign_in/",
        data={
            "username": username,
            "password": "password",
        }
    )


async def add_mock_user(db_session: AsyncSession, username: str) -> None:
    mock_email = f"mock{randint(1, 100_000_000)}{randint(1, 100_000_000)}@i.ai"
    user_schema = SUserSignUp(
        username=username,
        password=b"qwerty",
        email=mock_email,  # type: ignore
    )
    await user_repo.add(db_session, user_schema.model_dump())


async def create_spendings(
    qty: int,
    user_id: int,
    category_id: int | None,
    db_session: AsyncSession,
):
    if category_id is None:
        category = await user_spend_cat_service.get_default_category(
            user_id,
            db_session,
        )
        category_id = category.id

    for i in range(qty):
        transaction_to_create = STransactionCreateInDB(
            amount=1000 + i,
            description="Some description",
            date=None,
            user_id=user_id,
            category_id=category_id,
        )
        await spendings_repo.add(
            db_session,
            transaction_to_create.model_dump(),
        )


async def add_obj_to_db(obj, db_session: AsyncSession):
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    return obj
