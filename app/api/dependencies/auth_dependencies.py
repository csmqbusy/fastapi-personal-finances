from fastapi import Depends, Form
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.api.exceptions.auth_exceptions import (
    InvalidCredentialsError,
    InvalidTokenHTTPError,
    TokenNotFoundError,
    UserInactiveError,
    UserNotFoundError,
)
from app.db import get_db_session
from app.models import UserModel
from app.services.auth_service import (
    decode_access_token,
    verify_password,
)
from app.services.user_service import get_user_by_username


async def validate_credentials(
    username: str = Form(),
    password: str = Form(),
    db_session: AsyncSession = Depends(get_db_session),
) -> UserModel:
    user = await get_user_by_username(username, db_session)
    if not user:
        raise InvalidCredentialsError()
    if not verify_password(password, user.password):
        raise InvalidCredentialsError()
    return user


async def get_access_token_payload(request: Request) -> str:
    if access_token := request.cookies.get("access_token"):
        return access_token
    raise TokenNotFoundError()


async def validate_access_token(
    access_token: str = Depends(get_access_token_payload),
) -> dict:
    try:
        payload = decode_access_token(access_token)
    except InvalidTokenError:
        raise InvalidTokenHTTPError()
    return payload


async def get_verified_user(
    payload: dict = Depends(validate_access_token),
    db_session: AsyncSession = Depends(get_db_session),
) -> UserModel:
    username = payload.get("sub")
    if username:
        user = await get_user_by_username(username, db_session)
        if user:
            return user
    raise UserNotFoundError()


async def get_active_verified_user(
    user: UserModel = Depends(get_verified_user),
) -> UserModel:
    if user.active:
        return user
    raise UserInactiveError()
