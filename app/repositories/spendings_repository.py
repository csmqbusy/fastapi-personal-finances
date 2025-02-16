from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import SpendingsModel
from app.repositories.base_repository import BaseRepository


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
        query = select(self.model).filter_by(**params)
        query = query.order_by(self.model.id.desc())
        result = await session.execute(query)
        result = list(result.scalars().all())
        return result


spendings_repo = SpendingsRepository()
