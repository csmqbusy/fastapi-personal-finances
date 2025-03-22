from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import (
    get_active_verified_user,
    validate_credentials,
)
from app.api.exceptions.auth_exceptions import (
    EmailAlreadyExistsError,
    InvalidUsernameError,
    UsernameAlreadyExistsError,
)
from app.db import get_db_session
from app.exceptions.user_exceptions import (
    EmailAlreadyExists,
    UsernameAlreadyExists,
)
from app.models import UserModel
from app.schemas.user_schemas import SUserShortInfo, SUserSignUp
from app.services.auth_service import (
    create_access_token,
    hash_password,
    validate_username,
)
from app.services.user_service import create_user

router = APIRouter()


@router.post(
    "/sign_up/",
    summary="Create new user",
    status_code=status.HTTP_201_CREATED,
)
async def sign_up_user(
    user: SUserSignUp,
    db_session: AsyncSession = Depends(get_db_session),
) -> SUserShortInfo:
    user.password = hash_password(user.password.decode())
    if not validate_username(user.username):
        raise InvalidUsernameError()
    try:
        user_from_db = await create_user(user, db_session)
    except UsernameAlreadyExists:
        raise UsernameAlreadyExistsError()
    except EmailAlreadyExists:
        raise EmailAlreadyExistsError()
    return SUserShortInfo.model_validate(user_from_db)


@router.post(
    "/sign_in/",
    summary="Authenticate a user",
)
async def login(
    response: Response,
    user: UserModel = Depends(validate_credentials),
) -> dict:
    payload = {"sub": user.username}
    access_token = create_access_token(payload=payload)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
    )

    return {
        "sign_in": "Success!",
    }


@router.post(
    "/logout/",
    summary="Finish the user session",
)
async def logout(
    response: Response,
) -> dict:
    response.delete_cookie(key="access_token")
    return {
        "logout": "Success!",
    }


@router.get(
    "/me/",
    summary="Get current user info",
)
async def auth_user_get_info(
    user: UserModel = Depends(get_active_verified_user),
) -> SUserShortInfo:
    return SUserShortInfo.model_validate(user)
