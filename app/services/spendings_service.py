from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.categories_exceptions import CategoryNotFound
from app.exceptions.spending_exceptions import SpendingNotFound
from app.repositories import spendings_repo
from app.schemas.spendings_schemas import (
    SSpendingCreate,
    SSpendingCreateInDB,
    SSpendingResponse,
    SSpendingUpdatePartial,
    SSpendingUpdatePartialInDB,
)
from app.services.users_spending_categories_service import user_spend_cat_service


async def add_spending_to_db(
    spending: SSpendingCreate,
    user_id: int,
    session: AsyncSession,
):
    category_name = spending.category_name
    if not category_name:
        category_name = settings.app.default_spending_category_name
    category_id = await _get_category_id(user_id, category_name, session)
    spending_to_create = SSpendingCreateInDB(
        amount=spending.amount,
        description=spending.description,
        user_id=user_id,
        category_id=category_id,
    )
    spending = await spendings_repo.add(
        session,
        spending_to_create.model_dump(),
    )
    spending_out = SSpendingResponse.model_validate(spending)
    spending_out.category_name = category_name
    return spending_out


async def update_spending(
    spending_id: int,
    user_id: int,
    spending_update_obj: SSpendingUpdatePartial,
    session: AsyncSession,
) -> SSpendingResponse:
    spending = await spendings_repo.get_spending_with_category(
        session,
        spending_id,
    )
    if not spending or spending.user_id != user_id:
        raise SpendingNotFound

    if spending_update_obj.category_name:
        category_name = spending_update_obj.category_name
        category_id = await _get_category_id(category_name, user_id, session)
    else:
        category_name = spending.spending_category.name
        category_id = spending.spending_category.id

    spending_to_update = SSpendingUpdatePartialInDB(
        amount=spending_update_obj.amount,
        description=spending_update_obj.description,
        category_id=category_id,
    )
    updated_spending = await spendings_repo.update(
        session,
        spending_id,
        spending_to_update.model_dump(exclude_none=True),
    )
    spending_out = SSpendingResponse.model_validate(updated_spending)
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


async def get_spending(
    spending_id: int,
    user_id: int,
    session: AsyncSession,
):
    spending = await spendings_repo.get_spending_with_category(
        session, spending_id
    )
    if not spending or spending.user_id != user_id:
        raise SpendingNotFound

    spending_response = SSpendingResponse(
        amount=spending.amount,
        description=spending.description,
        category_name=spending.category.category_name,
        date=spending.date,
        id=spending.id,
    )
    return spending_response


async def _get_category_id(
    user_id: int,
    category_name: str,
    session: AsyncSession,
) -> int:
    category = await user_spend_cat_service.get_category(
        user_id,
        category_name,
        session,
    )
    if not category:
        raise CategoryNotFound
    return category.id
