from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SavingGoalsModel
from app.repositories.base_repository import BaseRepository
from app.schemas.common_schemas import SortParam
from app.schemas.saving_goals_schemas import GoalStatus


class SavingGoalsRepository(BaseRepository[SavingGoalsModel]):
    def __init__(self):
        super().__init__(SavingGoalsModel)

    async def get_goals_from_db(
        self,
        session: AsyncSession,
        user_id: int,
        min_current_amount: int | None = None,
        max_current_amount: int | None = None,
        min_target_amount: int | None = None,
        max_target_amount: int | None = None,
        name_search_term: str | None = None,
        desc_search_term: str | None = None,
        start_date_from: date | None = None,
        start_date_to: date | None = None,
        target_date_from: date | None = None,
        target_date_to: date | None = None,
        end_date_from: date | None = None,
        end_date_to: date | None = None,
        status: GoalStatus | None = None,
        sort_params: list[SortParam] | None = None,
    ) -> list[SavingGoalsModel]:
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
        )

        filters = []
        if min_current_amount:
            filters.append(self.model.current_amount >= min_current_amount)
        if max_current_amount:
            filters.append(self.model.current_amount <= max_current_amount)
        if min_target_amount:
            filters.append(self.model.target_amount >= min_target_amount)
        if max_target_amount:
            filters.append(self.model.target_amount <= max_target_amount)
        if name_search_term:
            filters.append(self.model.name.ilike(f"%{name_search_term}%"))
        if desc_search_term:
            filters.append(self.model.description.ilike(f"%{desc_search_term}%"))
        if start_date_from:
            filters.append(self.model.start_date >= start_date_from)
        if start_date_to:
            filters.append(self.model.start_date <= start_date_to)
        if target_date_from:
            filters.append(self.model.target_date >= target_date_from)
        if target_date_to:
            filters.append(self.model.target_date <= target_date_to)
        if end_date_from:
            filters.append(self.model.end_date >= end_date_from)
        if end_date_to:
            filters.append(self.model.end_date <= end_date_to)
        if status:
            filters.append(self.model.status == status)

        if filters:
            query = query.where(and_(*filters))

        if sort_params:
            for param in sort_params:
                if param.order_direction == "asc":
                    query = query.order_by(
                        getattr(self.model, param.order_by).asc()
                    )
                else:
                    query = query.order_by(
                        getattr(self.model, param.order_by).desc()
                    )

        result = await session.execute(query)
        return list(result.scalars().all())


saving_goals_repo = SavingGoalsRepository()
