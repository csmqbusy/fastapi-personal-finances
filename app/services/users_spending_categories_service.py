from app.core.config import settings
from app.repositories import user_spend_cat_repo
from app.schemas.spending_category_schemas import SSpendingCategoryOut
from app.services.base_categories_service import BaseCategoriesService


class UserSpendingCategoriesService(BaseCategoriesService):
    def __init__(
        self,
        category_repo,
        default_category_name: str,
        out_schema,
    ):
        super().__init__(
            category_repo=category_repo,
            default_category_name=default_category_name,
            out_schema=out_schema,
        )


user_spend_cat_service = UserSpendingCategoriesService(
    user_spend_cat_repo,
    settings.app.default_spending_category_name,
    SSpendingCategoryOut,
)
