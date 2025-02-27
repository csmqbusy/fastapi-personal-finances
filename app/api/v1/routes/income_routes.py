from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.api.exceptions.operations_exceptions import CategoryNotFoundError, \
    TransactionNotFoundError
from app.db import get_db_session
from app.exceptions.categories_exceptions import CategoryNotFound
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.models import UserModel
from app.schemas.transaction_category_schemas import STransactionCategoryOut
from app.schemas.transactions_schemas import (
    STransactionCreate,
    STransactionResponse,
)
from app.services.income_service import income_service
from app.services.users_income_categories_service import user_income_cat_service

router = APIRouter(prefix="/income")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create new income",
)
async def income_add(
    income: STransactionCreate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionResponse:
    try:
        return await income_service.add_transaction_to_db(
            income,
            user.id,
            db_session,
        )
    except CategoryNotFound:
        raise CategoryNotFoundError()


@router.get(
    "/categories/",
    status_code=status.HTTP_200_OK,
    summary="Get user's income categories",
)
async def income_categories_get(
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[STransactionCategoryOut]:
    return await user_income_cat_service.get_user_categories(user.id, db_session)


@router.get(
    "/{income_id}/",
    status_code=status.HTTP_200_OK,
    summary="Get income details",
)
async def income_get(
    income_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionResponse:
    try:
        return await income_service.get_transaction(
            income_id,
            user.id,
            db_session,
        )
    except TransactionNotFound:
        raise TransactionNotFoundError()
