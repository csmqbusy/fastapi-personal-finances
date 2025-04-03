from app.models import IncomeModel, UsersIncomeCategoriesModel
from app.repositories import BaseTransactionsRepository

income_repo = BaseTransactionsRepository(
    model=IncomeModel,
    tx_categories_model=UsersIncomeCategoriesModel,
)
