from app.models import SpendingsModel
from app.repositories import BaseTransactionsRepository

spendings_repo = BaseTransactionsRepository(model=SpendingsModel)
