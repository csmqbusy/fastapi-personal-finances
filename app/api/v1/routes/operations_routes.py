from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import get_active_verified_user
from app.db import get_db_session
from app.models import UserModel
from app.schemas.spendings_schemas import SSpendingIn, SSpendingOut
from app.services.spendings_service import add_spending_to_db

router = APIRouter()


@router.post("/add_spending/")
async def add_spending(
    spending: SSpendingIn,
    user: UserModel = Depends(get_active_verified_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SSpendingOut:
    return await add_spending_to_db(spending, user.id, db_session)
