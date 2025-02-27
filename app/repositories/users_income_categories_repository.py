from app.models import UsersIncomeCategoriesModel
from app.repositories.base_categories_repository import BaseCategoriesRepository

user_income_cat_repo = BaseCategoriesRepository(
    model=UsersIncomeCategoriesModel,
)
