from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.api.exceptions.operations_exceptions import CategoryNotFoundError
from app.db import get_db_session
from app.exceptions.categories_exceptions import CategoryNotFound
from app.models import UserModel
from app.schemas.transactions_schemas import (
    STransactionCreate,
    STransactionResponse,
)
from app.services.income_service import income_service


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
