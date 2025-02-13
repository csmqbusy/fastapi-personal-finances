from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import IdIntPKMixin


if TYPE_CHECKING:
    from app.models import SpendingCategoriesModel


class SpendingsModel(IdIntPKMixin, Base):
    __tablename__ = "spendings"

    amount: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(100), nullable=True)
    date: Mapped[datetime] = mapped_column(
        server_default=text("TIMEZONE ('utc', now())"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    spending_category: Mapped["SpendingCategoriesModel"] = relationship(
        "SpendingCategoriesModel",
        lazy="joined"
    )
