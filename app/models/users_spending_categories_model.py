from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.mixins import IdIntPKMixin


class UsersSpendingCategoriesModel(IdIntPKMixin, Base):
    __tablename__ = "users_spending_categories"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
