from random import randint
from typing import TypeVar, Type, Any

import factory
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Base, UserModel
from app.repositories import user_repo, spendings_repo
from app.schemas.transaction_category_schemas import STransactionCategoryOut
from app.schemas.transactions_schemas import STransactionCreateInDB
from app.schemas.user_schemas import SUserSignUp
from app.services import user_spend_cat_service
from tests.factories import UserFactory, UsersSpendingCategoriesFactory

AnySQLAlchemyModel = TypeVar("AnySQLAlchemyModel", bound=Base)
AnyFactory = TypeVar("AnyFactory", bound=factory.Factory)


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


async def add_obj_to_db(obj: AnySQLAlchemyModel, db_session: AsyncSession):
    db_session.add(obj)
    await db_session.commit()
    await db_session.refresh(obj)
    return obj


async def add_obj_to_db_all(
    objects: list[AnySQLAlchemyModel],
    db_session: AsyncSession,
) -> None:
    for obj in objects:
        db_session.add(obj)
        await db_session.commit()


async def create_batch(
    db_session: AsyncSession,
    qty: int,
    factory_: Type[AnyFactory],
    factory_params: dict[str, Any] | None = None,
):
    """
    Creates a batch of objects of the transferred factory in the database.
    """
    for _ in range(qty):
        obj = factory_()
        if factory_params:
            for param in factory_params:
                setattr(obj, param, factory_params[param])

        await add_obj_to_db(obj, db_session)


async def auth_another_user(
    db_session: AsyncSession,
    client: AsyncClient,
) -> UserModel:
    user = await add_obj_to_db(UserFactory(), db_session)
    await client.post(
        url=f"{settings.api.prefix_v1}/sign_in/",
        data={
            "username": user.username,
            "password": "password",
        }
    )
    return user


async def create_n_categories(
    categories_qty: int,
    user_id: int,
    db_session: AsyncSession,
) -> list[int]:
    """Return list of created categories id's."""
    categories_ids = []
    for _ in range(categories_qty):
        category = UsersSpendingCategoriesFactory(user_id=user_id)
        await add_obj_to_db(category, db_session)
        categories_ids.append(category.id)
    return categories_ids


async def add_default_spendings_category(
    user_id: int,
    db_session: AsyncSession,
) -> STransactionCategoryOut:
    await user_spend_cat_service.add_user_default_category(user_id, db_session)
    return await user_spend_cat_service.get_default_category(user_id, db_session)
