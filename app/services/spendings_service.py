from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.exceptions.categories_exceptions import CategoryNotFound
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.models import SpendingsModel
from app.repositories import spendings_repo, user_spend_cat_repo
from app.schemas.spendings_schemas import (
    SSpendingCreate,
    SSpendingCreateInDB,
    SSpendingResponse,
    SSpendingUpdatePartial,
    SSpendingUpdatePartialInDB,
)


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

    spending_to_update = SSpendingUpdatePartialInDB(
        amount=spending_update_obj.amount,
        description=spending_update_obj.description,
    )

    new_cat_name = spending_update_obj.category_name
    if new_cat_name and new_cat_name != spending.category.category_name:
        new_category = await user_spend_cat_repo.get_one_by_filter(
            session,
            dict(user_id=user_id, category_name=new_cat_name),
        )
        if new_category is None:
            raise CategoryNotFound
        spending.category_id = new_category.id
        await session.commit()
        await session.refresh(spending)

    updated_spending = await spendings_repo.update(
        session,
        spending_id,
        spending_to_update.model_dump(exclude_none=True),
    )

    spending_response = SSpendingResponse(
        amount=updated_spending.amount,
        description=updated_spending.description,
        category_name=spending.category.category_name,
        date=updated_spending.date,
        id=updated_spending.id,
    )
    return spending_response


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


async def get_all_spendings_by_category(
    category_id: int,
    user_id: int,
    session: AsyncSession,
) -> list[SpendingsModel]:
    spendings = await spendings_repo.get_all_by_filter(
        session,
        dict(category_id=category_id, user_id=user_id),
    )
    return spendings


async def _get_category_id(
    user_id: int,
    category_name: str,
    session: AsyncSession,
) -> int:
    category = await user_spend_cat_repo.get_one_by_filter(
        session,
        dict(user_id=user_id, category_name=category_name),
    )
    if not category:
        raise CategoryNotFound
    return category.id
