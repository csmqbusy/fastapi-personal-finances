from app.models import UsersSpendingCategoriesModel
from app.repositories.base_categories_repository import BaseCategoriesRepository

user_spend_cat_repo = BaseCategoriesRepository(
    model=UsersSpendingCategoriesModel,
)
