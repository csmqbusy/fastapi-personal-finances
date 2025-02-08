from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.mixins import IdIntPKMixin


class SpendingCategoriesModel(IdIntPKMixin, Base):
    __tablename__ = "spending_categories"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
