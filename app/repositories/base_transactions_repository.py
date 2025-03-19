from datetime import datetime
from typing import Type

from sqlalchemy import select, and_, func, desc, ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import UsersSpendingCategoriesModel
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
        """
        Get transactions with `category` relation.
        """
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

        filters: list[ColumnElement[bool]] = []
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

    async def get_annual_summary_from_db(
        self,
        session: AsyncSession,
        user_id: int,
        year: int,
    ) -> list:
        """
        SELECT SUM(amount) AS amount, category_name, EXTRACT(MONTH FROM date) AS month
        FROM spendings
        INNER JOIN users_spending_categories
           ON spendings.category_id = users_spending_categories.id
        WHERE spendings.user_id = {user_id}
          AND EXTRACT(YEAR FROM date) = {year}
        GROUP BY category_name, EXTRACT(MONTH FROM date)
        ORDER BY month, amount DESC, category_name

        result example: [(700, 'Beer', Decimal('1'))]
        designations: [(summary amount, category name, month number)]
        """
        query = (
            select(
                func.sum(self.model.amount).label("amount"),
                UsersSpendingCategoriesModel.category_name,
                func.extract("month", self.model.date).label("month"),
            )
            .join(
                UsersSpendingCategoriesModel,
                self.model.category_id == UsersSpendingCategoriesModel.id,
            )
            .where(
                and_(
                    self.model.user_id == user_id,
                    func.extract("year", self.model.date) == year,
                )
            )
            .group_by(
                UsersSpendingCategoriesModel.category_name,
                func.extract("month", self.model.date),
            )
            .order_by(
                "month",
                desc("amount"),
                UsersSpendingCategoriesModel.category_name,
            )
        )
        result = await session.execute(query)
        return list(result)

    async def get_monthly_summary_from_db(
        self,
        session: AsyncSession,
        user_id: int,
        year: int,
        month: int,
    ) -> list:
        """
        SELECT SUM(amount) AS amount, category_name, EXTRACT(DAY FROM date) AS day
        FROM spendings
        INNER JOIN users_spending_categories
           ON spendings.category_id = users_spending_categories.id
        WHERE spendings.user_id=12
          AND EXTRACT(YEAR FROM date)=2025
          AND EXTRACT(MONTH FROM date)=3
        GROUP BY category_name, EXTRACT(DAY FROM date)
        ORDER BY day, amount DESC, category_name

        result example: [(700, 'Beer', Decimal('1'))]
        designations: [(summary amount, category name, day number)]
        """
        query = (
            select(
                func.sum(self.model.amount).label("amount"),
                UsersSpendingCategoriesModel.category_name,
                func.extract("day", self.model.date).label("day"),
            )
            .join(
                UsersSpendingCategoriesModel,
                self.model.category_id == UsersSpendingCategoriesModel.id,
            )
            .where(
                and_(
                    self.model.user_id == user_id,
                    func.extract("year", self.model.date) == year,
                    func.extract("month", self.model.date) == month,
                )
            )
            .group_by(
                UsersSpendingCategoriesModel.category_name,
                func.extract("day", self.model.date),
            )
            .order_by(
                "day",
                desc("amount"),
                UsersSpendingCategoriesModel.category_name,
            )
        )
        result = await session.execute(query)
        return list(result)
