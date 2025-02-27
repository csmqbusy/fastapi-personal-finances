from sqlalchemy import UniqueConstraint

from app.models.base_categories_model import BaseCategoriesModel


class UsersIncomeCategoriesModel(BaseCategoriesModel):
    __tablename__ = "users_income_categories"

    __table_args__ = (
        UniqueConstraint(
            "user_id", "category_name", name="uq_user_income_category",
        ),
    )
