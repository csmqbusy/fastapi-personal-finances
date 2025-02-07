from fastapi import (
    APIRouter,
    Depends,
    status,
    Response,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.authentication import (
    validate_credentials,
    get_active_verified_user,
)
from app.api.exceptions.authentication import (
    UsernameAlreadyExistsError,
    EmailAlreadyExistsError,
)
from app.services.auth import (
    hash_password,
    create_access_token,
)
from app.db import get_db_session
from app.exceptions.user import UsernameAlreadyExists, EmailAlreadyExists
from app.models import UserModel
from app.schemes.user import SUserSignUp, SUserShortInfo
from app.services.user import create_user

router = APIRouter()


@router.post(
    "/login/",
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
    "/registration/",
    summary="Create new user",
    status_code=status.HTTP_201_CREATED,
)
async def sign_up_user(
    user: SUserSignUp,
    db_session: AsyncSession = Depends(get_db_session),
) -> SUserShortInfo:
    user.password = hash_password(user.password.decode())
    try:
        user_from_db = await create_user(user, db_session)
    except UsernameAlreadyExists:
        raise UsernameAlreadyExistsError()
    except EmailAlreadyExists:
        raise EmailAlreadyExistsError()
    return SUserShortInfo.model_validate(user_from_db)


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
