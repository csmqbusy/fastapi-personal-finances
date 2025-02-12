from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.mixins import IdIntPKMixin


class UsersSpendingCategoriesModel(IdIntPKMixin, Base):
    __tablename__ = "users_spending_categories"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("spending_categories.id"),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "category_id", name="uq_user_category"),
    )
