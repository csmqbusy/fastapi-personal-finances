from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.api.exceptions.operations_exceptions import SpendingNotFoundError
from app.db import get_db_session
from app.exceptions.spending_exceptions import SpendingNotFound
from app.models import UserModel
from app.schemas.spending_category_schemas import (
    SSpendingCategoryIn,
    SSpendingCategoryOut,
)
from app.schemas.spendings_schemas import (
    SSpendingCreate,
    SSpendingResponse,
    SSpendingUpdatePartial,
)
from app.services import spend_cat_service
from app.services.spendings_service import (
    add_spending_to_db,
    delete_spending,
    update_spending,
    get_spending,
)

router = APIRouter()


@router.post("/spending/add/", status_code=status.HTTP_201_CREATED)
async def spending_add(
    spending: SSpendingCreate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingResponse:
    return await add_spending_to_db(spending, user.id, db_session)


@router.get("/spending/get/{}/", status_code=status.HTTP_200_OK)
async def spending_get(
    spending_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingResponse:
    try:
        return await get_spending(spending_id, user.id, db_session)
    except SpendingNotFound:
        raise SpendingNotFoundError()


@router.patch("/spending/update/{}/", status_code=status.HTTP_200_OK)
async def spending_update(
    spending_id: int,
    spending_update_obj: SSpendingUpdatePartial,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingResponse:
    try:
        updated_spending = await update_spending(
            spending_id,
            user.id,
            spending_update_obj,
            db_session,
        )
    except SpendingNotFound:
        raise SpendingNotFoundError()
    return updated_spending


@router.delete("/spending/delete/{}/", status_code=status.HTTP_200_OK)
async def spending_delete(
    spending_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        await delete_spending(spending_id, user.id, db_session)
    except SpendingNotFound:
        raise SpendingNotFoundError()
    return {
        "delete": "ok",
        "id": spending_id,
    }


@router.post("/spending_categories/add/", status_code=status.HTTP_201_CREATED)
async def spending_category_add(
    spending_category: SSpendingCategoryIn,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingCategoryOut:
    return await spend_cat_service.add_category_to_db(
        spending_category.name,
        user.id,
        db_session,
    )
