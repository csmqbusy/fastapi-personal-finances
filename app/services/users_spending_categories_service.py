from app.core.config import settings
from app.repositories import user_spend_cat_repo, spendings_repo
from app.schemas.spending_category_schemas import STransactionCategoryOut
from app.services.base_categories_service import BaseCategoriesService


user_spend_cat_service = BaseCategoriesService(
    category_repo=user_spend_cat_repo,
    transaction_repo=spendings_repo,
    default_category_name=settings.app.default_spending_category_name,
    out_schema=STransactionCategoryOut,
)
