import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UsersSpendingCategoriesModel
from app.repositories import spendings_repo, user_repo
from app.schemas.transactions_schemas import STransactionCreateInDB
from app.services import user_spend_cat_service
from tests.integration.helpers import add_mock_user


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, create_user",
    [
        (
            "Balls",
            True,
        ),
        (
            "Doping",
            False,
        ),
    ]
)
async def test_get_transaction_with_category(
    db_session: AsyncSession,
    category_name: str,
    create_user: bool,
) -> None:
    mock_user_username = "GOLOVIN"
    if create_user:
        await add_mock_user(db_session, mock_user_username)
    user = await user_repo.get_by_username(db_session, mock_user_username)

    category = await user_spend_cat_service.add_category_to_db(
        user.id,
        category_name,
        db_session,
    )

    transaction_to_create = STransactionCreateInDB(
        amount=1000,
        description="Some description",
        date=None,
        user_id=user.id,
        category_id=category.id,
    )
    spending = await spendings_repo.add(
        db_session,
        transaction_to_create.model_dump(),
    )

    spending_from_db = await spendings_repo.get_transaction_with_category(
        db_session,
        spending.id,
    )
    assert type(spending_from_db.category) is UsersSpendingCategoriesModel
    assert spending_from_db.category.id == category.id
    assert spending_from_db.category.category_name == category.category_name
