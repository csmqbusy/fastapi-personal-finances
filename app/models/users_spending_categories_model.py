from sqlalchemy import UniqueConstraint

from app.models.base_categories_model import BaseCategoriesModel


class UsersSpendingCategoriesModel(BaseCategoriesModel):
    __tablename__ = "users_spending_categories"

    __table_args__ = (
        UniqueConstraint("user_id", "category_name", name="uq_user_category"),
    )
