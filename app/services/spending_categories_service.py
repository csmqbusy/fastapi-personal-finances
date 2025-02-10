from app.core.config import settings
from app.repositories import spend_cat_repo, user_spend_cat_repo
from app.schemas.spending_category_schemas import SSpendingCategoryOut
from app.services.base_categories_service import BaseCategoriesService


class SpendingCategoriesService(BaseCategoriesService):
    def __init__(
        self,
        category_repo,
        user_categories_repo,
        default_category_name,
        out_schema,
    ):
        super().__init__(
            category_repo=category_repo,
            user_categories_repo=user_categories_repo,
            default_category_name=default_category_name,
            out_schema=out_schema,
        )


spend_cat_service = SpendingCategoriesService(
    spend_cat_repo,
    user_spend_cat_repo,
    settings.app.default_spending_category_name,
    SSpendingCategoryOut,
)
