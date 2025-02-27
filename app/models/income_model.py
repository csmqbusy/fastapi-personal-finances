from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_transactions_model import BaseTranscationsModel

if TYPE_CHECKING:
    from app.models import UsersIncomeCategoriesModel


class IncomeModel(BaseTranscationsModel):
    __tablename__ = "income"

    category_id: Mapped[int] = mapped_column(
        ForeignKey("users_income_categories.id"),
        nullable=False,
    )

    category: Mapped["UsersIncomeCategoriesModel"] = relationship(
        "UsersIncomeCategoriesModel",
    )
