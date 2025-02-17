from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.api.dependencies.pagination_dependencies import get_pagination_params
from app.api.exceptions.operations_exceptions import (
    SpendingNotFoundError,
    CategoryNotFoundError,
    CategoryAlreadyExistsError,
    CategoryNameNotFoundError,
    CannotDeleteDefaultCategoryError,
    MissingCategoryError,
)
from app.db import get_db_session
from app.exceptions.categories_exceptions import (
    CategoryNotFound,
    CategoryAlreadyExists,
    CategoryNameNotFound,
    CannotDeleteDefaultCategory,
    MissingCategory,
)
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.models import UserModel
from app.schemas.pagination_schemas import SPagination
from app.schemas.spending_category_schemas import (
    SSpendingCategoryCreate,
    SSpendingCategoryOut,
    SSpendingCategoryUpdate,
    SpendingsOnDeleteActions,
)
from app.schemas.spendings_schemas import (
    SSpendingCreate,
    SSpendingResponse,
    SSpendingUpdatePartial,
)
from app.services import spendings_service
from app.services.common_services import apply_pagination
from app.services.users_spending_categories_service import user_spend_cat_service

router = APIRouter()


@router.post(
    "/spending/",
    status_code=status.HTTP_201_CREATED,
    summary="Create new spending",
)
async def spending_add(
    spending: SSpendingCreate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingResponse:
    try:
        return await spendings_service.add_transaction_to_db(
            spending,
            user.id,
            db_session,
        )
    except CategoryNotFound:
        raise CategoryNotFoundError()


@router.get(
    "/spending/recent/",
    status_code=status.HTTP_200_OK,
    summary="Get recent spendings across all categories",
)
async def spending_get_recent(
    pagination: SPagination = Depends(get_pagination_params),
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        all_spendings = await spendings_service.get_all_user_transactions(
            user_id=user.id,
            session=db_session,
        )
        selected_spendings = apply_pagination(all_spendings, pagination)
    except MissingCategory:
        raise MissingCategoryError()

    if len(selected_spendings) == 0:
        raise SpendingNotFoundError()
    return selected_spendings


@router.get(
    "/spending/{spending_id}/",
    status_code=status.HTTP_200_OK,
    summary="Get spending details",
)
async def spending_get(
    spending_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingResponse:
    try:
        return await spendings_service.get_transaction(
            spending_id,
            user.id,
            db_session,
        )
    except TransactionNotFound:
        raise SpendingNotFoundError()


@router.get(
    "/spending/by_category/{category_name}/",
    status_code=status.HTTP_200_OK,
    summary="Get spendings by category",
)
async def spending_get_by_category(
    category_name: str,
    pagination: SPagination = Depends(get_pagination_params),
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        all_spendings = await spendings_service.get_all_transactions_by_category(
            category_name=category_name,
            user_id=user.id,
            session=db_session,
        )
        selected_spendings = apply_pagination(all_spendings, pagination)
    except MissingCategory:
        raise MissingCategoryError()

    if len(selected_spendings) == 0:
        raise SpendingNotFoundError()
    return selected_spendings


@router.patch(
    "/spending/{spending_id}/",
    status_code=status.HTTP_200_OK,
    summary="Partial update spending details",
)
async def spending_update(
    spending_id: int,
    spending_update_obj: SSpendingUpdatePartial,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingResponse:
    try:
        updated_spending = await spendings_service.update_transaction(
            spending_id,
            user.id,
            spending_update_obj,
            db_session,
        )
    except TransactionNotFound:
        raise SpendingNotFoundError()
    except CategoryNotFound:
        raise CategoryNotFoundError()
    return updated_spending


@router.delete(
    "/spending/{spending_id}/",
    status_code=status.HTTP_200_OK,
    summary="Delete spending",
)
async def spending_delete(
    spending_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        await spendings_service.delete_transaction(
            spending_id,
            user.id,
            db_session,
        )
    except TransactionNotFound:
        raise SpendingNotFoundError()
    return {
        "delete": "ok",
        "id": spending_id,
    }


@router.post(
    "/spending_categories/",
    status_code=status.HTTP_201_CREATED,
    summary="Create new spending category",
)
async def spending_category_add(
    spending_category: SSpendingCategoryCreate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingCategoryOut:
    try:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            spending_category.category_name,
            db_session,
        )
    except CategoryAlreadyExists:
        raise CategoryAlreadyExistsError()
    return category


@router.get(
    "/spending_categories/",
    status_code=status.HTTP_200_OK,
    summary="Get user's spending categories",
)
async def spending_categories_get(
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    return await user_spend_cat_service.get_user_categories(user.id, db_session)


@router.patch(
    "/spending_categories/{category_name}/",
    status_code=status.HTTP_200_OK,
    summary="Partial update spending category details",
)
async def spending_category_update(
    category_name: str,
    spending_category_update_obj: SSpendingCategoryUpdate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingCategoryOut:
    try:
        category = await user_spend_cat_service.update_category(
            category_name,
            user.id,
            spending_category_update_obj,
            db_session,
        )
    except CategoryNotFound:
        raise CategoryNotFoundError()
    except CategoryAlreadyExists:
        raise CategoryAlreadyExistsError()
    return category


@router.delete(
    "/spending_categories/{category_name}/",
    status_code=status.HTTP_200_OK,
    summary="Delete spending category",
)
async def spending_category_delete(
    category_name: str,
    handle_spendings_on_deletion: SpendingsOnDeleteActions,
    new_category_name: str | None = None,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    try:
        await user_spend_cat_service.delete_category(
            category_name=category_name,
            user_id=user.id,
            transactions_actions=handle_spendings_on_deletion,
            new_category_name=new_category_name,
            session=db_session,
        )
    except CannotDeleteDefaultCategory:
        raise CannotDeleteDefaultCategoryError()
    except CategoryNotFound:
        raise CategoryNotFoundError()
    except CategoryNameNotFound:
        raise CategoryNameNotFoundError()

