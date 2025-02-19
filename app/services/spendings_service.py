from app.core.config import settings
from app.repositories import spendings_repo, user_spend_cat_repo
from app.schemas.spendings_schemas import (
    STransactionCreate,
    SSpendingCreateInDB,
    SSpendingResponse,
    SSpendingUpdatePartial,
)
from app.services.base_transactions_service import TransactionsService


spendings_service = TransactionsService(
    tx_repo=spendings_repo,
    tx_categories_repo=user_spend_cat_repo,
    default_tx_category_name=settings.app.default_spending_category_name,
    creation_schema=STransactionCreate,
    creation_in_db_schema=SSpendingCreateInDB,
    update_partial_in_db_schema=SSpendingUpdatePartial,
    out_schema=SSpendingResponse,
)
