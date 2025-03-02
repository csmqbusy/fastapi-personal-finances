from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.saving_goals_repository import (
    saving_goals_repo,
    SavingGoalsRepository,
)
from app.schemas.saving_goals_schemas import (
    SSavingGoalCreate,
    SSavingGoalCreateInDB,
    SSavingGoalResponse,
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
    ):
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



saving_goals_service = SavingGoalsService(
    repository=saving_goals_repo,
    creation_in_db_schema=SSavingGoalCreateInDB,
    out_schema=SSavingGoalResponse,
)
