from app.models import IncomeModel
from app.repositories import BaseTransactionsRepository

income_repo = BaseTransactionsRepository(model=IncomeModel)
