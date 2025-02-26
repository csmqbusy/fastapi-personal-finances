from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.mixins import IdIntPKMixin


class BaseCategoriesModel(IdIntPKMixin, Base):
    __abstract__ = True

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    category_name: Mapped[str] = mapped_column(String(50))
