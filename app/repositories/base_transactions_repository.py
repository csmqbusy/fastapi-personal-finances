from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.repositories.base_repository import BaseRepository
from app.schemas.transactions_schemas import SortParam


class BaseTransactionsRepository(BaseRepository):
    def __init__(self, model):
        super().__init__(model=model)

    async def get_transaction_with_category(
        self,
        session: AsyncSession,
        transaction_id: int,
    ):
        query = (
            select(self.model)
            .filter_by(id=transaction_id)
            .options(joinedload(self.model.category))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_transactions(
        self,
        session: AsyncSession,
        query_params: dict,
        description_search_term: str | None = None,
        datetime_from: datetime | None = None,
        datetime_to: datetime | None = None,
        sort_params: list[SortParam] | None = None,
    ):
        query = select(self.model).filter_by(**query_params)

        if description_search_term:
            query = query.filter(
                self.model.description.ilike(f"%{description_search_term}%")
            )

        if datetime_from:
            query = query.where(self.model.date >= datetime_from)
        if datetime_to:
            query = query.where(self.model.date <= datetime_to)

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
