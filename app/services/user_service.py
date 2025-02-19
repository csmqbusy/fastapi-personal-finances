from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.user_exceptions import (
    UsernameAlreadyExists,
    EmailAlreadyExists,
)
from app.models import UserModel
from app.repositories import user_repo
from app.schemas.user_schemas import SUserSignUp
from app.services.users_spending_categories_service import user_spend_cat_service


async def create_user(
    user: SUserSignUp,
    session: AsyncSession,
) -> UserModel:
    if not (await _check_unique_username(user.username, session)):
        raise UsernameAlreadyExists
    if not (await _check_unique_email(user.email, session)):
        raise EmailAlreadyExists

    user_from_db = await user_repo.add(session, user.model_dump())
    await user_spend_cat_service.add_user_default_category(
        user_from_db.id,
        session,
    )
    return user_from_db


async def get_user_by_username(
    username: str,
    session: AsyncSession,
) -> UserModel | None:
    return await user_repo.get_by_username(session, username)


async def _check_unique_username(
    username: str,
    session: AsyncSession,
) -> bool:
    user = await get_user_by_username(username, session)
    if user is None:
        return True
    return False


async def _check_unique_email(
    email: EmailStr,
    session: AsyncSession,
) -> bool:
    user = await user_repo.get_by_email(session, email)
    if user is None:
        return True
    return False
