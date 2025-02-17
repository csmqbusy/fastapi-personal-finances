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
        result = await self.get_all(
            params=params,
            order_by="id",
            order_direction="desc",
            session=session,
        )
        return result


spendings_repo = SpendingsRepository()
