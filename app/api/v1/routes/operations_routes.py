from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.db import get_db_session
from app.models import UserModel
from app.schemas.spending_category_schemas import (
    SSpendingCategoryIn,
    SSpendingCategoryOut,
)
from app.schemas.spendings_schemas import SSpendingIn, SSpendingOut
from app.services import spend_cat_service
from app.services.spendings_service import add_spending_to_db

router = APIRouter()


@router.post("/add_spending/")
async def add_spending(
    spending: SSpendingIn,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingOut:
    return await add_spending_to_db(spending, user.id, db_session)


@router.post("/add_spending_category/")
async def add_spending_category(
    spending_category: SSpendingCategoryIn,
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingCategoryOut:
    return await spend_cat_service.add_category_to_db(
        spending_category.name,
        db_session,
    )
