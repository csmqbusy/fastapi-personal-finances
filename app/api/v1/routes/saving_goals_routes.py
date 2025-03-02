from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.api.exceptions.operations_exceptions import GoalNotFoundError
from app.db import get_db_session
from app.exceptions.saving_goals_exceptions import GoalNotFound
from app.models import UserModel
from app.schemas.saving_goals_schemas import (
    SSavingGoalCreate,
    SSavingGoalResponse,
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
