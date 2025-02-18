from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import SpendingsModel
from app.repositories.base_repository import BaseRepository
from app.schemas.spendings_schemas import SortParam


class SpendingsRepository(BaseRepository[SpendingsModel]):
    def __init__(self):
        super().__init__(model=SpendingsModel)

    async def get_transaction_with_category(
        self,
        session: AsyncSession,
        spending_id: int,
    ) -> SpendingsModel:
        query = (
            select(self.model)
            .filter_by(id=spending_id)
            .options(joinedload(self.model.category))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_transactions_by_category(
        self,
        session: AsyncSession,
        params: dict,
    ):
        result = await self.get_all(
            params=params,
            order_by="id",
            order_direction="desc",
            session=session,
        )
        return result

    async def get_transactions(
        self,
        session: AsyncSession,
        query_params: dict,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_params: list[SortParam] | None = None,
    ):
        query = select(self.model).filter_by(**query_params)

        if date_from:
            query = query.where(self.model.date >= date_from)
        if date_to:
            query = query.where(self.model.date <= date_to)

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


spendings_repo = SpendingsRepository()
