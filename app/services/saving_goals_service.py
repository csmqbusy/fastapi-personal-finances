from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.saving_goals_exceptions import (
    GoalNotFound,
)
from app.repositories.saving_goals_repository import (
    saving_goals_repo,
    SavingGoalsRepository,
)
from app.schemas.saving_goals_schemas import (
    SSavingGoalCreate,
    SSavingGoalCreateInDB,
    SSavingGoalResponse,
    SSavingGoalUpdatePartial,
)


class SavingGoalsService:
    def __init__(
        self,
        repository: SavingGoalsRepository,
        creation_in_db_schema: Type[SSavingGoalCreateInDB],
        out_schema: Type[SSavingGoalResponse],
    ):
        self.repo = repository
        self.creation_in_db_schema = creation_in_db_schema
        self.out_schema = out_schema

    async def set_goal(
        self,
        session: AsyncSession,
        goal: SSavingGoalCreate,
        user_id: int,
    ) -> SSavingGoalResponse:
        goal_to_create = self.creation_in_db_schema(
            name=goal.name,
            description=goal.description,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            target_date=goal.target_date,
            start_date=goal.start_date,
            end_date=None,
            user_id=user_id,
        )
        goal_from_db = await self.repo.add(session, goal_to_create.model_dump())
        return self.out_schema.model_validate(goal_from_db)

    async def get_goal(
        self,
        goal_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> SSavingGoalResponse:
        goal = await self.repo.get(session, goal_id)
        if not goal or goal.user_id != user_id:
            raise GoalNotFound
        return self.out_schema.model_validate(goal)

    async def delete_goal(
        self,
        goal_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> None:
        goal = await self.get_goal(goal_id, user_id, session)
        await self.repo.delete(session, goal.id)

    async def update_goal(
        self,
        goal_id: int,
        user_id: int,
        goal_update_obj: SSavingGoalUpdatePartial,
        session: AsyncSession,
    ) -> SSavingGoalResponse:
        goal = await self.get_goal(goal_id, user_id, session)

        updated_goal = await self.repo.update(
            session,
            goal.id,
            goal_update_obj.model_dump(exclude_none=True),
        )
        return self.out_schema.model_validate(updated_goal)

saving_goals_service = SavingGoalsService(
    repository=saving_goals_repo,
    creation_in_db_schema=SSavingGoalCreateInDB,
    out_schema=SSavingGoalResponse,
)
