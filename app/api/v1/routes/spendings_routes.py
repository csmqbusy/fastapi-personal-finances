from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.api.dependencies.common_dependenceis import get_csv_params
from app.api.dependencies.operations_dependencies import (
    get_amount_range,
    get_categories_params,
    get_date_range,
    get_pagination_params,
    get_transactions_sort_params,
)
from app.api.exceptions.operations_exceptions import (
    CannotDeleteDefaultCategoryError,
    CategoryAlreadyExistsError,
    CategoryNameNotFoundError,
    CategoryNotFoundError,
    TransactionNotFoundError,
)
from app.db import get_db_session
from app.exceptions.categories_exceptions import (
    CannotDeleteDefaultCategory,
    CategoryAlreadyExists,
    CategoryNameNotFound,
    CategoryNotFound,
)
from app.exceptions.transaction_exceptions import TransactionNotFound
from app.models import UserModel
from app.schemas.common_schemas import (
    SAmountRange,
    SDatetimeRange,
    SPagination,
)
from app.schemas.transaction_category_schemas import (
    SCategoryQueryParams,
    STransactionCategoryCreate,
    STransactionCategoryOut,
    STransactionCategoryUpdate,
    TransactionsOnDeleteActions,
)
from app.schemas.transactions_schemas import (
    DayTransactionsSummary,
    MonthTransactionsSummary,
    STransactionCreate,
    STransactionResponse,
    STransactionsSortParams,
    STransactionsSummary,
    STransactionUpdatePartial,
)
from app.services import spendings_service
from app.services.common_service import (
    apply_pagination,
    get_filename_with_utc_datetime,
    make_csv_from_pydantic_models,
)
from app.services.users_spending_categories_service import user_spend_cat_service

router = APIRouter(prefix="/spendings")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create new spending",
)
async def spending_add(
    spending: STransactionCreate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionResponse:
    try:
        return await spendings_service.add_transaction_to_db(
            spending,
            user.id,
            db_session,
        )
    except CategoryNotFound:
        raise CategoryNotFoundError()


@router.get(
    "/categories/",
    status_code=status.HTTP_200_OK,
    summary="Get user's spending categories",
)
async def spendings_categories_get(
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[STransactionCategoryOut]:
    return await user_spend_cat_service.get_user_categories(user.id, db_session)


@router.get(
    "/summary/",
    status_code=status.HTTP_200_OK,
    summary="Get spendings summary",
)
async def spendings_summary_get(
    user: UserModel = Depends(get_active_verified_user),
    categories_params: list[SCategoryQueryParams] = Depends(get_categories_params),
    amount_params: SAmountRange = Depends(get_amount_range),
    description_search_term: str | None = Query(None),
    datetime_range: SDatetimeRange = Depends(get_date_range),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[STransactionsSummary]:
    try:
        spendings_summary = await spendings_service.get_summary(
            session=db_session,
            user_id=user.id,
            categories_params=categories_params,
            amount_params=amount_params,
            search_term=description_search_term,
            datetime_range=datetime_range,
        )
    except CategoryNotFound:
        raise CategoryNotFoundError()
    return spendings_summary


@router.get(
    "/summary/chart/",
    status_code=status.HTTP_200_OK,
    summary="Get chart with spendings by category",
)
async def spendings_summary_chart_get(
    user: UserModel = Depends(get_active_verified_user),
    chart_type: str | None = Query(None),
    categories_params: list[SCategoryQueryParams] = Depends(get_categories_params),
    amount_params: SAmountRange = Depends(get_amount_range),
    description_search_term: str | None = Query(None),
    datetime_range: SDatetimeRange = Depends(get_date_range),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    chart: bytes = await spendings_service.get_summary_chart(
        session=db_session,
        user_id=user.id,
        chart_type=chart_type,
        categories_params=categories_params,
        amount_params=amount_params,
        search_term=description_search_term,
        datetime_range=datetime_range,
    )
    return Response(content=chart, media_type="image/png")


@router.get(
    "/summary/{year}/",
    status_code=status.HTTP_200_OK,
    summary="Get annual spendings summary",
    response_model=None,
)
async def spendings_annual_summary_get(
    user: UserModel = Depends(get_active_verified_user),
    year: int = Path(),
    in_csv: bool = Depends(get_csv_params),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[MonthTransactionsSummary] | Response:
    summary = await spendings_service.get_annual_summary(
        session=db_session,
        user_id=user.id,
        year=year,
    )
    if in_csv:
        prepared_data = spendings_service.prepare_annual_summary_for_csv(
            period_summary=summary,
        )
        output_csv = make_csv_from_pydantic_models(prepared_data)
        filename = get_filename_with_utc_datetime(
            f"{year}_spendings_summary", "csv"
        )
        return Response(
            content=output_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
    return summary


@router.get(
    "/summary/chart/{year}/",
    status_code=status.HTTP_200_OK,
    summary="Get annual spendings summary chart",
)
async def spendings_annual_summary_chart_get(
    user: UserModel = Depends(get_active_verified_user),
    year: int = Path(),
    split_by_category: bool = Query(False),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    chart: bytes = await spendings_service.get_annual_summary_chart(
        session=db_session,
        user_id=user.id,
        year=year,
        transactions_type="spendings",
        split_by_category=split_by_category,
    )
    return Response(content=chart, media_type="image/png")


@router.get(
    "/summary/{year}/{month}/",
    status_code=status.HTTP_200_OK,
    summary="Get monthly spendings summary",
    response_model=None,
)
async def spendings_monthly_summary_get(
    year: int,
    month: int = Path(ge=1, le=12),
    in_csv: bool = Depends(get_csv_params),
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[DayTransactionsSummary] | Response:
    summary = await spendings_service.get_monthly_summary(
        session=db_session,
        user_id=user.id,
        year=year,
        month=month,
    )
    if in_csv:
        prepared_data = spendings_service.prepare_monthly_summary_for_csv(
            period_summary=summary,
        )
        output_csv = make_csv_from_pydantic_models(prepared_data)
        filename = get_filename_with_utc_datetime(
            f"{year}_{month}_spendings_summary", "csv"
        )
        return Response(
            content=output_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
    return summary


@router.get(
    "/summary/chart/{year}/{month}/",
    status_code=status.HTTP_200_OK,
    summary="Get monthly spendings summary chart",
)
async def spendings_monthly_summary_chart_get(
    user: UserModel = Depends(get_active_verified_user),
    year: int = Path(),
    month: int = Path(ge=1, le=12),
    split_by_category: bool = Query(False),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    chart: bytes = await spendings_service.get_monthly_summary_chart(
        session=db_session,
        user_id=user.id,
        year=year,
        month=month,
        transactions_type="spendings",
        split_by_category=split_by_category,
    )
    return Response(content=chart, media_type="image/png")


@router.get(
    "/{spending_id}/",
    status_code=status.HTTP_200_OK,
    summary="Get spending details",
)
async def spending_get(
    spending_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionResponse:
    try:
        return await spendings_service.get_transaction(
            spending_id,
            user.id,
            db_session,
        )
    except TransactionNotFound:
        raise TransactionNotFoundError()


@router.patch(
    "/{spending_id}/",
    status_code=status.HTTP_200_OK,
    summary="Partial update spending details",
)
async def spending_update(
    spending_id: int,
    spending_update_obj: STransactionUpdatePartial,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionResponse:
    try:
        updated_spending = await spendings_service.update_transaction(
            spending_id,
            user.id,
            spending_update_obj,
            db_session,
        )
    except TransactionNotFound:
        raise TransactionNotFoundError()
    except CategoryNotFound:
        raise CategoryNotFoundError()
    return updated_spending


@router.delete(
    "/{spending_id}/",
    status_code=status.HTTP_200_OK,
    summary="Delete spending",
)
async def spending_delete(
    spending_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        await spendings_service.delete_transaction(
            spending_id,
            user.id,
            db_session,
        )
    except TransactionNotFound:
        raise TransactionNotFoundError()
    return {
        "delete": "ok",
        "id": spending_id,
    }


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=None,
)
async def spendings_get_all(
    user: UserModel = Depends(get_active_verified_user),
    categories_params: list[SCategoryQueryParams] = Depends(get_categories_params),
    amount_params: SAmountRange = Depends(get_amount_range),
    description_search_term: str | None = Query(None),
    datetime_range: SDatetimeRange = Depends(get_date_range),
    pagination: SPagination = Depends(get_pagination_params),
    sort_params: STransactionsSortParams = Depends(get_transactions_sort_params),
    in_csv: bool = Depends(get_csv_params),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[STransactionResponse] | Response:
    try:
        spendings = await spendings_service.get_transactions(
            session=db_session,
            user_id=user.id,
            categories_params=categories_params,
            amount_params=amount_params,
            search_term=description_search_term,
            datetime_range=datetime_range,
            sort_params=sort_params,
        )
    except CategoryNotFound:
        raise CategoryNotFoundError()
    if in_csv:
        output_csv = make_csv_from_pydantic_models(spendings)
        filename = get_filename_with_utc_datetime("spendings", "csv")
        return Response(
            content=output_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
    spendings = apply_pagination(spendings, pagination)
    return spendings


@router.post(
    "/categories/",
    status_code=status.HTTP_201_CREATED,
    summary="Create new spending category",
)
async def spending_category_add(
    spending_category: STransactionCategoryCreate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionCategoryOut:
    try:
        category = await user_spend_cat_service.add_category_to_db(
            user.id,
            spending_category.category_name,
            db_session,
        )
    except CategoryAlreadyExists:
        raise CategoryAlreadyExistsError()
    return category


@router.patch(
    "/categories/{category_name}/",
    status_code=status.HTTP_200_OK,
    summary="Partial update spending category details",
)
async def spending_category_update(
    category_name: str,
    spending_category_update_obj: STransactionCategoryUpdate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionCategoryOut:
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
    "/categories/{category_name}/",
    status_code=status.HTTP_200_OK,
    summary="Delete spending category",
)
async def spending_category_delete(
    category_name: str,
    handle_spendings_on_deletion: TransactionsOnDeleteActions,
    new_category_name: str | None = None,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    category_name = category_name.strip()
    if new_category_name:
        new_category_name = new_category_name.strip()

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

    return {
        "delete": "ok",
        "category_name": category_name,
    }
