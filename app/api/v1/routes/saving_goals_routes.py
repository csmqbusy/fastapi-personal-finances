from fastapi import APIRouter, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import get_active_verified_user
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
from app.schemas.saving_goals_schemas import (
    SSavingGoalCreate,
    SSavingGoalResponse,
    SSavingGoalUpdatePartial,
    SSavingGoalProgress,
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
