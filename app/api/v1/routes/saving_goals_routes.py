from fastapi import APIRouter, status, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.api.dependencies.common_dependenceis import get_csv_params
from app.api.dependencies.operations_dependencies import (
    get_pagination_params,
    get_transactions_sort_params,
)
from app.api.dependencies.saving_goals_dependencies import (
    get_start_date_range,
    get_target_date_range,
    get_end_date_range,
    get_current_amount_range,
    get_target_amount_range,
)
from app.api.exceptions.operations_exceptions import (
    GoalNotFoundError,
    GoalCurrentAmountError,
)
from app.db import get_db_session
from app.exceptions.saving_goals_exceptions import (
    GoalNotFound,
    GoalCurrentAmountInvalid,
)
from app.models import UserModel
from app.schemas.common_schemas import SAmountRange, SPagination, SDateRange
from app.schemas.saving_goals_schemas import (
    SSavingGoalCreate,
    SSavingGoalResponse,
    SSavingGoalUpdatePartial,
    SSavingGoalProgress,
    GoalStatus,
    SGoalsSortParams,
)
from app.services.common_service import (
    apply_pagination,
    make_csv_from_pydantic_models,
    get_filename_with_utc_datetime,
)
from app.services.saving_goals_service import saving_goals_service


router = APIRouter(prefix="/goals")


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Set saving goal",
)
async def saving_goal_set(
    goal: SSavingGoalCreate,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSavingGoalResponse:
    return await saving_goals_service.set_goal(db_session, goal, user.id)


@router.get(
    "/progress/{goal_id}/",
    status_code=status.HTTP_200_OK,
    summary="Get saving goal progress details",
)
async def saving_goal_progress_get(
    goal_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSavingGoalProgress:
    try:
        return await saving_goals_service.get_goal_progress(
            goal_id,
            user.id,
            db_session,
        )
    except GoalNotFound:
        raise GoalNotFoundError()


@router.get(
    "/{goal_id}/",
    status_code=status.HTTP_200_OK,
    summary="Get saving goal details",
)
async def saving_goal_get(
    goal_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSavingGoalResponse:
    try:
        return await saving_goals_service.get_goal(
            goal_id,
            user.id,
            db_session,
        )
    except GoalNotFound:
        raise GoalNotFoundError()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Get all saving goals",
    response_model=None,
)
async def saving_goals_get_all(
    user: UserModel = Depends(get_active_verified_user),
    current_amount_params: SAmountRange = Depends(get_current_amount_range),
    target_amount_params: SAmountRange = Depends(get_target_amount_range),
    name_search_term: str | None = Query(None),
    description_search_term: str | None = Query(None),
    start_date_range: SDateRange = Depends(get_start_date_range),
    target_date_range: SDateRange = Depends(get_target_date_range),
    end_date_range: SDateRange = Depends(get_end_date_range),
    goal_status: GoalStatus | None = Query(None),
    pagination: SPagination = Depends(get_pagination_params),
    sort_params: SGoalsSortParams = Depends(get_transactions_sort_params),
    in_csv: bool = Depends(get_csv_params),
    db_session: AsyncSession = Depends(get_db_session),
) -> list[SSavingGoalResponse] | Response:
    goals = await saving_goals_service.get_goals_all(
        session=db_session,
        user_id=user.id,
        current_amount_range=current_amount_params,
        target_amount_range=target_amount_params,
        name_search_term=name_search_term,
        description_search_term=description_search_term,
        start_date_range=start_date_range,
        target_date_range=target_date_range,
        end_date_range=end_date_range,
        status=goal_status,
        sort_params=sort_params,
    )
    if in_csv:
        output_csv = make_csv_from_pydantic_models(goals)
        filename = get_filename_with_utc_datetime("saving_goals", "csv")
        return Response(
            content=output_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                },
            )
    goals = apply_pagination(goals, pagination)
    return goals


@router.delete(
    "/{goal_id}/",
    status_code=status.HTTP_200_OK,
    summary="Delete saving goal",
)
async def saving_goal_delete(
    goal_id: int,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict:
    try:
        await saving_goals_service.delete_goal(
            goal_id,
            user.id,
            db_session,
        )
    except GoalNotFound:
        raise GoalNotFoundError()
    return {
        "delete": "ok",
        "id": goal_id,
    }


@router.patch(
    "/update_amount/{goal_id}/",
    status_code=status.HTTP_200_OK,
    summary="Partial update saving goal details",
)
async def saving_goal_update_amount(
    goal_id: int,
    payment: int = Query(
        description="It can be any integer, but the total value of "
                    "`current_amount` cannot be less than 0"
    ),
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSavingGoalResponse:
    try:
        return await saving_goals_service.update_current_amount(
            goal_id,
            user.id,
            payment,
            db_session,
        )
    except GoalNotFound:
        raise GoalNotFoundError()
    except GoalCurrentAmountInvalid:
        raise GoalCurrentAmountError()


@router.patch(
    "/{goal_id}/",
    status_code=status.HTTP_200_OK,
    summary="Partial update saving goal details",
)
async def saving_goal_update(
    goal_id: int,
    goal_update_obj: SSavingGoalUpdatePartial,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSavingGoalResponse:
    try:
        updated_spending = await saving_goals_service.update_goal(
            goal_id,
            user.id,
            goal_update_obj,
            db_session,
        )
    except GoalNotFound:
        raise GoalNotFoundError()
    return updated_spending
