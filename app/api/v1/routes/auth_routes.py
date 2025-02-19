from fastapi import (
    APIRouter,
    Depends,
    status,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth_dependencies import (
    validate_credentials,
    get_active_verified_user,
)
from app.api.exceptions.auth_exceptions import (
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
    InvalidUsernameError,
)
from app.services.auth_service import (
    hash_password,
    create_access_token,
    validate_username,
)
from app.db import get_db_session
from app.exceptions.user_exceptions import (
    UsernameAlreadyExists,
    EmailAlreadyExists,
)
from app.models import UserModel
from app.schemas.user_schemas import SUserSignUp, SUserShortInfo
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
):
    payload = {"sub": user.username}
    access_token = create_access_token(payload=payload)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax"
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
):
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
