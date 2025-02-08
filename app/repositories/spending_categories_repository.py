from app.models import SpendingCategoriesModel
from app.repositories.base_repository import BaseRepository


class SpendingCategoriesRepository(BaseRepository[SpendingCategoriesModel]):
    def __init__(self):
        super().__init__(SpendingCategoriesModel)


spending_categories_repo = SpendingCategoriesRepository()
