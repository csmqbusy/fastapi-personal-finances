from fastapi import APIRouter, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.api.dependencies.operations_dependencies import (
    get_transactions_query_params,
    get_amount_range,
    get_date_range,
    get_pagination_params,
    get_transactions_sort_params,
)
from app.api.exceptions.operations_exceptions import (
    CategoryNotFoundError,
    TransactionNotFoundError,
    CategoryAlreadyExistsError,
)
from app.db import get_db_session
from app.exceptions.categories_exceptions import (
    CategoryNotFound,
    CategoryAlreadyExists,
)
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.models import UserModel
from app.schemas.date_range_schemas import SDatetimeRange
from app.schemas.pagination_schemas import SPagination
from app.schemas.transaction_category_schemas import (
    STransactionCategoryOut,
    STransactionCategoryCreate,
)
from app.schemas.transactions_schemas import (
    STransactionCreate,
    STransactionResponse,
    STransactionUpdatePartial,
    STransactionsQueryParams,
    SAmountRange,
    STransactionsSortParams,
)
from app.services.common_service import apply_pagination
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


@router.patch(
    "/{income_id}/",
    status_code=status.HTTP_200_OK,
    summary="Partial update income details",
)
async def income_update(
    income_id: int,
    income_update_obj: STransactionUpdatePartial,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionResponse:
    try:
        updated_income = await income_service.update_transaction(
            income_id,
            user.id,
            income_update_obj,
            db_session,
        )
    except TransactionNotFound:
        raise TransactionNotFoundError()
    except CategoryNotFound:
        raise CategoryNotFoundError()
    return updated_income


@router.delete(
    "/{income_id}/",
    status_code=status.HTTP_200_OK,
    summary="Delete income",
)
async def income_delete(
    income_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        await income_service.delete_transaction(
            income_id,
            user.id,
            db_session,
        )
    except TransactionNotFound:
        raise TransactionNotFoundError()
    return {
        "delete": "ok",
        "id": income_id,
    }


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Get income",
)
async def income_get(
    user: UserModel = Depends(get_active_verified_user),
    query_params: STransactionsQueryParams = Depends(get_transactions_query_params),
    amount_params: SAmountRange = Depends(get_amount_range),
    description_search_term: str | None = Query(None),
    datetime_range: SDatetimeRange = Depends(get_date_range),
    pagination: SPagination = Depends(get_pagination_params),
    sort_params: STransactionsSortParams = Depends(get_transactions_sort_params),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[STransactionResponse]:
    try:
        income = await income_service.get_transactions(
            session=db_session,
            user_id=user.id,
            query_params=query_params,
            amount_params=amount_params,
            search_term=description_search_term,
            datetime_range=datetime_range,
            sort_params=sort_params,
        )
    except CategoryNotFound:
        raise CategoryNotFoundError()
    income = apply_pagination(income, pagination)
    return income


@router.post(
    "/categories/",
    status_code=status.HTTP_201_CREATED,
    summary="Create new income category",
)
async def income_category_add(
    income_category: STransactionCategoryCreate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionCategoryOut:
    try:
        category = await user_income_cat_service.add_category_to_db(
            user.id,
            income_category.category_name,
            db_session,
        )
    except CategoryAlreadyExists:
        raise CategoryAlreadyExistsError()
    return category
