from datetime import datetime
from typing import Type

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.base_transactions_model import BaseTranscationsModel
from app.repositories.base_repository import BaseRepository
from app.schemas.common_schemas import SortParam


class BaseTransactionsRepository(BaseRepository[BaseTranscationsModel]):
    def __init__(self, model: Type[BaseTranscationsModel]):
        super().__init__(model=model)

    async def get_transaction_with_category(
        self,
        session: AsyncSession,
        transaction_id: int,
    ) -> BaseTranscationsModel | None:
        query = (
            select(self.model)
            .filter_by(id=transaction_id)
            .options(joinedload(self.model.category))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_transactions_from_db(
        self,
        session: AsyncSession,
        user_id: int,
        categories_ids: list[int] | None = None,
        min_amount: int | None = None,
        max_amount: int | None = None,
        description_search_term: str | None = None,
        datetime_from: datetime | None = None,
        datetime_to: datetime | None = None,
        sort_params: list[SortParam] | None = None,
    ) -> list[BaseTranscationsModel]:
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
        )

        filters = []
        if categories_ids:
            filters.append(self.model.category_id.in_(categories_ids))
        if description_search_term:
            filters.append(self.model.description.ilike(
                f"%{description_search_term}%"),
            )
        if min_amount:
            filters.append(self.model.amount >= min_amount)
        if max_amount:
            filters.append(self.model.amount <= max_amount)
        if datetime_from:
            filters.append(self.model.date >= datetime_from)
        if datetime_to:
            filters.append(self.model.date <= datetime_to)

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

        query = query.options(joinedload(self.model.category))

        result = await session.execute(query)
        return list(result.scalars().all())
