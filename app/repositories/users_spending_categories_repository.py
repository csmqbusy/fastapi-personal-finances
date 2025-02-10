from app.models import UsersSpendingCategoriesModel
from app.repositories.base_repository import BaseRepository


class UserSpendingCategoriesRepository(
    BaseRepository[UsersSpendingCategoriesModel]
):
    def __init__(self):
        super().__init__(UsersSpendingCategoriesModel)


user_spend_cat_repo = UserSpendingCategoriesRepository()
