from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.base_categories_model import BaseCategoriesModel
from app.models.mixins import IdIntPKMixin


class BaseTranscationsModel(IdIntPKMixin, Base):
    __abstract__ = True

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

    # category_id must be defined in the inherited class as the foreign key
    # to the desired transaction table.
    category_id: Mapped[int]

    # category should be defined in the inherited class as a relationship
    # to the desired transaction model.
    category: Mapped["BaseCategoriesModel"]
