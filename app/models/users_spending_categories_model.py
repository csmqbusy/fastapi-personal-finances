from sqlalchemy import ForeignKey, UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.mixins import IdIntPKMixin


class UsersSpendingCategoriesModel(IdIntPKMixin, Base):
    __tablename__ = "users_spending_categories"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    category_name: Mapped[str] = mapped_column(String(50))

    __table_args__ = (
        UniqueConstraint("user_id", "category_name", name="uq_user_category"),
    )
