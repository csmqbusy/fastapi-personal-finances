from app.models import SpendingsModel, UsersSpendingCategoriesModel
from app.repositories import BaseTransactionsRepository

spendings_repo = BaseTransactionsRepository(
    model=SpendingsModel,
    tx_categories_model=UsersSpendingCategoriesModel,
)
