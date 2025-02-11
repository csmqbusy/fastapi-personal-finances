from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.spending_exceptions import SpendingNotFound
from app.repositories import spendings_repo
from app.schemas.spendings_schemas import (
    SSpendingIn,
    SSpendingCreate,
    SSpendingOut,
)
from app.services import spend_cat_service


async def add_spending_to_db(
    spending: SSpendingIn,
    user_id: int,
    session: AsyncSession,
):
    category_name = spending.category_name
    if not category_name:
        category_name = settings.app.default_spending_category_name
    category_id = await _get_category_id(category_name, user_id, session)
    spending_to_create = SSpendingCreate(
        amount=spending.amount,
        description=spending.description,
        category_id=category_id,
        user_id=user_id,
    )
    spending = await spendings_repo.add(
        session,
        spending_to_create.model_dump(),
    )
    spending_out = SSpendingOut.model_validate(spending)
    spending_out.category_name = category_name
    return spending_out


async def delete_spending(
    spending_id: int,
    user_id: int,
    session: AsyncSession,
):
    spending = await spendings_repo.get(session, spending_id)
    if not spending or spending.user_id != user_id:
        raise SpendingNotFound
    await spendings_repo.delete(session, spending_id)


async def _get_category_id(
    category_name: str,
    user_id: int,
    session: AsyncSession,
) -> int:
    category_exists = await spend_cat_service.is_category_exists(
        category_name,
        session,
    )
    if category_exists:
        category = await spend_cat_service.get_category_by_name(
            category_name,
            session,
        )
    else:
        category = await spend_cat_service.add_category_to_db(
            category_name,
            user_id,
            session,
        )
    return category.id
