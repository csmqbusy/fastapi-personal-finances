from datetime import date
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.saving_goals_exceptions import (
    GoalCurrentAmountInvalid,
    GoalNotFound,
)
from app.models import SavingGoalsModel
from app.repositories.saving_goals_repository import (
    SavingGoalsRepository,
    saving_goals_repo,
)
from app.schemas.common_schemas import SAmountRange, SDateRange
from app.schemas.saving_goals_schemas import (
    GoalStatus,
    SGoalsSortParams,
    SSavingGoalCreate,
    SSavingGoalCreateInDB,
    SSavingGoalProgress,
    SSavingGoalResponse,
    SSavingGoalUpdatePartial,
)
from app.services.common_service import parse_sort_params_for_query


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
        """
        Create saving goal.
        """
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
        if goal.current_amount == goal.target_amount:
            goal_to_create.status = GoalStatus.COMPLETED
            goal_to_create.end_date = date.today()

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

        new_current_amount = goal_update_obj.current_amount
        new_target_amount = goal_update_obj.target_amount

        if new_current_amount and new_target_amount:
            if new_current_amount == new_target_amount:
                await self._complete_saving_goal(goal_id, session)
        elif new_current_amount and not new_target_amount:
            if new_current_amount >= goal.target_amount:
                goal_update_obj.current_amount = goal.target_amount
                await self._complete_saving_goal(goal_id, session)

        updated_goal = await self.repo.update(
            session,
            goal.id,
            goal_update_obj.model_dump(exclude_none=True),
        )
        return self.out_schema.model_validate(updated_goal)

    async def get_goal_progress(
        self,
        goal_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> SSavingGoalProgress:
        goal = await self.get_goal(goal_id, user_id, session)

        rest_amount = goal.target_amount - goal.current_amount
        percentage_progress = self.get_percentage(
            goal.current_amount,
            goal.target_amount,
        )
        days_left = self.get_days_between_dates(goal.target_date)
        expected_daily_payment = self.get_expected_daily_payment(
            rest_amount,
            days_left,
        )

        goal_progress = SSavingGoalProgress(
            current_amount=goal.current_amount,
            target_amount=goal.target_amount,
            rest_amount=rest_amount,
            percentage_progress=percentage_progress,
            days_left=days_left,
            expected_daily_payment=expected_daily_payment,
        )
        return goal_progress

    async def update_current_amount(
        self,
        goal_id: int,
        user_id: int,
        payment: int,
        session: AsyncSession,
    ) -> SSavingGoalResponse:
        goal = await self.get_goal(goal_id, user_id, session)

        new_amount = goal.current_amount + payment
        if new_amount < 0:
            raise GoalCurrentAmountInvalid
        if new_amount >= goal.target_amount:
            new_amount = goal.target_amount
            await self._complete_saving_goal(goal_id, session)

        updated_goal = await self.repo.update(
            session,
            goal.id,
            {"current_amount": new_amount},
        )
        return self.out_schema.model_validate(updated_goal)

    async def get_goals_all(
        self,
        session: AsyncSession,
        user_id: int,
        current_amount_range: SAmountRange | None = None,
        target_amount_range: SAmountRange | None = None,
        name_search_term: str | None = None,
        description_search_term: str | None = None,
        start_date_range: SDateRange | None = None,
        target_date_range: SDateRange | None = None,
        end_date_range: SDateRange | None = None,
        status: GoalStatus | None = None,
        sort_params: SGoalsSortParams | None = None,
    ) -> list[SSavingGoalResponse]:
        if sort_params:
            parsed_sort_params = parse_sort_params_for_query(sort_params)
        else:
            parsed_sort_params = None

        if current_amount_range:
            min_current_amount = current_amount_range.min_amount
            max_current_amount = current_amount_range.max_amount
        else:
            min_current_amount = None
            max_current_amount = None

        if target_amount_range:
            min_target_amount = target_amount_range.min_amount
            max_target_amount = target_amount_range.max_amount
        else:
            min_target_amount = None
            max_target_amount = None

        if start_date_range:
            start_date_from = start_date_range.start
            start_date_to = start_date_range.end
        else:
            start_date_from = None
            start_date_to = None

        if target_date_range:
            target_date_from = target_date_range.start
            target_date_to = target_date_range.end
        else:
            target_date_from = None
            target_date_to = None

        if end_date_range:
            end_date_from = end_date_range.start
            end_date_to = end_date_range.end
        else:
            end_date_from = None
            end_date_to = None

        goals = await self.repo.get_goals_from_db(
            session=session,
            user_id=user_id,
            min_current_amount=min_current_amount,
            max_current_amount=max_current_amount,
            min_target_amount=min_target_amount,
            max_target_amount=max_target_amount,
            name_search_term=name_search_term,
            desc_search_term=description_search_term,
            start_date_from=start_date_from,
            start_date_to=start_date_to,
            target_date_from=target_date_from,
            target_date_to=target_date_to,
            end_date_from=end_date_from,
            end_date_to=end_date_to,
            status=status,
            sort_params=parsed_sort_params,
        )
        result = []
        for goal in goals:
            if self._is_goal_overdue(goal):
                await self.make_saving_goal_overdue(goal.id, session)
                await session.refresh(goal)

            goal_out = self.out_schema.model_validate(goal)
            result.append(goal_out)
        return result

    async def _complete_saving_goal(
        self,
        goal_id: int,
        session: AsyncSession,
    ):
        await self.repo.update(
            session,
            goal_id,
            {
                "status": GoalStatus.COMPLETED,
                "end_date": date.today(),
            },
        )

    @staticmethod
    def _is_goal_overdue(
        goal: SavingGoalsModel,
    ) -> bool:
        return date.today() > goal.target_date

    async def make_saving_goal_overdue(
        self,
        goal_id: int,
        session: AsyncSession,
    ):
        await self.repo.update(
            session,
            goal_id,
            {
                "status": GoalStatus.OVERDUE,
            },
        )

    @staticmethod
    def get_percentage(first_num: int, second_num: int) -> float:
        """
        first_num: The number whose percentage is to be calculated.
        second_num: The number relative to which the percentage is calculated.
        """
        if second_num == 0:
            return 0
        return round(first_num / second_num * 100, 2)

    @staticmethod
    def get_days_between_dates(
        d1: date,
        d2: date = date.today(),
    ) -> int:
        delta = d2 - d1
        return abs(delta.days)

    @staticmethod
    def get_expected_daily_payment(rest_amount: int, days_left: int) -> int:
        if days_left == 0:
            return rest_amount
        return round(rest_amount / days_left)


saving_goals_service = SavingGoalsService(
    repository=saving_goals_repo,
    creation_in_db_schema=SSavingGoalCreateInDB,
    out_schema=SSavingGoalResponse,
)
