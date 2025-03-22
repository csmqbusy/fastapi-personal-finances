from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.services.common_service import (
    apply_pagination,
    get_filename_with_utc_datetime,
    make_csv_from_pydantic_models,
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
            transaction=income,
            user_id=user.id,
            session=db_session,
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
    "/summary/",
    status_code=status.HTTP_200_OK,
    summary="Get income summary",
)
async def income_summary_get(
    user: UserModel = Depends(get_active_verified_user),
    categories_params: list[SCategoryQueryParams] = Depends(get_categories_params),
    amount_params: SAmountRange = Depends(get_amount_range),
    description_search_term: str | None = Query(None),
    datetime_range: SDatetimeRange = Depends(get_date_range),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[STransactionsSummary]:
    try:
        income_summary = await income_service.get_summary(
            session=db_session,
            user_id=user.id,
            categories_params=categories_params,
            amount_params=amount_params,
            search_term=description_search_term,
            datetime_range=datetime_range,
        )
    except CategoryNotFound:
        raise CategoryNotFoundError()
    return income_summary


@router.get(
    "/summary/chart/",
    status_code=200,
    summary="Get chart with income by category",
)
async def income_summary_chart_get(
    user: UserModel = Depends(get_active_verified_user),
    chart_type: str | None = Query(None),
    categories_params: list[SCategoryQueryParams] = Depends(get_categories_params),
    amount_params: SAmountRange = Depends(get_amount_range),
    description_search_term: str | None = Query(None),
    datetime_range: SDatetimeRange = Depends(get_date_range),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    chart: bytes = await income_service.get_summary_chart(
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
    status_code=200,
    summary="Get annual income summary",
    response_model=None,
)
async def income_annual_summary_get(
    year: int,
    user: UserModel = Depends(get_active_verified_user),
    in_csv: bool = Depends(get_csv_params),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[MonthTransactionsSummary] | Response:
    summary = await income_service.get_annual_summary(
            session=db_session,
            user_id=user.id,
            year=year,
        )
    if in_csv:
        prepared_data = income_service.prepare_annual_summary_for_csv(
            period_summary=summary,
        )
        output_csv = make_csv_from_pydantic_models(prepared_data)
        filename = get_filename_with_utc_datetime(f"{year}_income_summary", "csv")
        return Response(
            content=output_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
    return summary


@router.get(
    "/summary/{year}/chart",
    status_code=200,
    summary="Get annual income summary chart",
)
async def income_annual_summary_chart_get(
    user: UserModel = Depends(get_active_verified_user),
    year: int = Path(),
    split_by_category: bool = Query(False),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    chart: bytes = await income_service.get_annual_summary_chart(
            session=db_session,
            user_id=user.id,
            year=year,
            transactions_type="income",
            split_by_category=split_by_category,
        )
    return Response(content=chart, media_type="image/png")


@router.get(
    "/summary/{year}/{month}/",
    status_code=200,
    summary="Get monthly income summary",
    response_model=None,
)
async def income_monthly_summary_get(
    year: int,
    month: Annotated[int, Path(ge=1, le=12)],
    in_csv: bool = Depends(get_csv_params),
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[DayTransactionsSummary] | Response:
    summary = await income_service.get_monthly_summary(
            session=db_session,
            user_id=user.id,
            year=year,
            month=month,
        )
    if in_csv:
        prepared_data = income_service.prepare_monthly_summary_for_csv(
            period_summary=summary,
        )
        output_csv = make_csv_from_pydantic_models(prepared_data)
        filename = get_filename_with_utc_datetime(
            f"{year}_{month}_income_summary", "csv"
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
    "/summary/{year}/{month}/chart/",
    status_code=200,
    summary="Get monthly income summary chart",
)
async def income_monthly_summary_chart_get(
    year: int,
    month: Annotated[int, Path(ge=1, le=12)],
    split_by_category: bool = Query(False),
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> Response:
    chart: bytes = await income_service.get_monthly_summary_chart(
            session=db_session,
            user_id=user.id,
            year=year,
            month=month,
            transactions_type="income",
            split_by_category=split_by_category,
        )
    return Response(content=chart, media_type="image/png")


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
    response_model=None,
)
async def income_get_all(
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
        income = await income_service.get_transactions(
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
        output_csv = make_csv_from_pydantic_models(income)
        filename = get_filename_with_utc_datetime("income", "csv")
        return Response(
            content=output_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
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


@router.patch(
    "/categories/{category_name}/",
    status_code=status.HTTP_200_OK,
    summary="Partial update income category details",
)
async def income_category_update(
    category_name: str,
    income_category_update_obj: STransactionCategoryUpdate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> STransactionCategoryOut:
    try:
        category = await user_income_cat_service.update_category(
            category_name,
            user.id,
            income_category_update_obj,
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
    summary="Delete income category",
)
async def income_category_delete(
    category_name: str,
    handle_income_on_deletion: TransactionsOnDeleteActions,
    new_category_name: str | None = None,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    category_name = category_name.strip()
    if new_category_name:
        new_category_name = new_category_name.strip()

    try:
        await user_income_cat_service.delete_category(
            category_name=category_name,
            user_id=user.id,
            transactions_actions=handle_income_on_deletion,
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
