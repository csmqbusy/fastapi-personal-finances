from app.core.config import settings
from app.repositories import user_income_cat_repo, income_repo
from app.schemas.transaction_category_schemas import STransactionCategoryOut
from app.services.base_categories_service import BaseCategoriesService


user_income_cat_service = BaseCategoriesService(
    category_repo=user_income_cat_repo,
    transaction_repo=income_repo,
    default_category_name=settings.app.default_income_category_name,
    out_schema=STransactionCategoryOut,
)
