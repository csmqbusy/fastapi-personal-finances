from enum import Enum

import pytest
from httpx import AsyncClient
from starlette import status

from app.core.config import settings


class RegistrationExpectedResponse(Enum):
    CREATED = 0
    USERNAME_EXISTS = 1
    EMAIL_EXISTS = 2


class LoginFailType(Enum):
    NO_FAIL = 0
    USERNAME_ERROR = 1
    PASSWORD_ERROR = 2


class RefreshFailType(Enum):
    NO_FAIL = 0
    NO_TOKEN = 1
    INVALID_TOKEN = 2


class GetInfoFailType(Enum):
    NO_FAIL = 0
    NO_ACCESS_TOKEN = 1
    INVALID_TOKEN = 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, password, email, status_code, expected_response",
    [
        (
            "mike",
            "password",
            "mike@example.com",
            status.HTTP_201_CREATED,
            RegistrationExpectedResponse.CREATED,
        ),
        (
            "mike",
            "password",
            "mike22@example.com",
            status.HTTP_409_CONFLICT,
            RegistrationExpectedResponse.USERNAME_EXISTS,
        ),
        (
            "john",
            "password",
            "mike@example.com",
            status.HTTP_409_CONFLICT,
            RegistrationExpectedResponse.EMAIL_EXISTS,
        ),
        (
            "john",
            "password",
            "john@example.com",
            status.HTTP_201_CREATED,
            RegistrationExpectedResponse.CREATED,
        ),
    ]
)
async def test_sign_up_user(
    client: AsyncClient,
    username: str,
    password: str,
    email: str,
    status_code: int,
    expected_response: RegistrationExpectedResponse,
):
    expected_json_answer = None
    if expected_response == RegistrationExpectedResponse.CREATED:
        expected_json_answer = {"username": username, "email": email}
    elif expected_response == RegistrationExpectedResponse.USERNAME_EXISTS:
        expected_json_answer = {"detail": "Username already exists."}
    elif expected_response == RegistrationExpectedResponse.EMAIL_EXISTS:
        expected_json_answer = {"detail": "Email already exists."}

    response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": username,
            "password": password,
            "email": email,
        }
    )
    assert response.status_code == status_code
    assert response.json() == expected_json_answer


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, password, email, status_code, fail_type, json_answer",
    [
        (
            "daniel",
            "password",
            "daniel@example.com",
            status.HTTP_200_OK,
            LoginFailType.NO_FAIL,
            {"sign_in": "Success!"}
        ),
        (
            "michael",
            "password",
            "michael@example.com",
            status.HTTP_401_UNAUTHORIZED,
            LoginFailType.USERNAME_ERROR,
            {"detail": "Could not validate credentials."},
        ),
        (
            "alice",
            "password",
            "alice@example.com",
            status.HTTP_401_UNAUTHORIZED,
            LoginFailType.PASSWORD_ERROR,
            {"detail": "Could not validate credentials."},
        ),
    ]
)
async def test_login(
    client: AsyncClient,
    username: str,
    password: str,
    email: str,
    status_code: int,
    fail_type: LoginFailType,
    json_answer: dict,
):
    signup_response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": username,
            "password": password,
            "email": email,
        }
    )
    assert signup_response.status_code == status.HTTP_201_CREATED

    if fail_type == LoginFailType.NO_FAIL:
        assert client.cookies.get("access_token") is None
        login_response = await client.post(
            url=f"{settings.api.prefix_v1}/sign_in/",
            data={
                "username": username,
                "password": password,
            }
        )
        assert login_response.status_code == status_code
        assert login_response.json() == json_answer
        assert client.cookies.get("access_token") is not None

    else:
        if fail_type == LoginFailType.USERNAME_ERROR:
            username = username + "_fail"
        elif fail_type == LoginFailType.PASSWORD_ERROR:
            password = password + "_fail"

        assert client.cookies.get("access_token") is None
        login_response = await client.post(
            url=f"{settings.api.prefix_v1}/sign_in/",
            data={
                "username": username,
                "password": password,
            }
        )
        assert login_response.status_code == status_code
        assert login_response.json() == json_answer
        assert client.cookies.get("access_token") is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, password, email, status_code, json_answer",
    [
        (
            "rodrigo",
            "password",
            "rodrigo@example.com",
            status.HTTP_200_OK,
            {"logout": "Success!"},
        ),
    ]
)
async def test_logout(
    client: AsyncClient,
    username: str,
    password: str,
    email: str,
    status_code: int,
    json_answer: dict,
):
    signup_response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": username,
            "password": password,
            "email": email,
        }
    )
    assert signup_response.status_code == status.HTTP_201_CREATED

    login_response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_in/",
        data={
            "username": username,
            "password": password,
        }
    )
    assert login_response.status_code == status.HTTP_200_OK

    logout_response = await client.post(
        url=f"{settings.api.prefix_v1}/logout/",
    )
    assert logout_response.status_code == status_code
    assert logout_response.json() == json_answer
    assert client.cookies.get("access_token") is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, password, email, status_code, fail_type",
    [
        (
            "andrew",
            "password",
            "andrew@example.com",
            status.HTTP_200_OK,
            GetInfoFailType.NO_FAIL,
        ),
        (
            "martin",
            "password",
            "martin@example.com",
            status.HTTP_401_UNAUTHORIZED,
            GetInfoFailType.NO_ACCESS_TOKEN,
        ),
        (
            "donald",
            "password",
            "donald@example.com",
            status.HTTP_401_UNAUTHORIZED,
            GetInfoFailType.INVALID_TOKEN,
        ),
    ]
)
async def test_auth_user_get_info(
    client: AsyncClient,
    username: str,
    password: str,
    email: str,
    status_code: int,
    fail_type: GetInfoFailType,
):
    signup_response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": username,
            "password": password,
            "email": email,
        }
    )
    assert signup_response.status_code == status.HTTP_201_CREATED

    login_response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_in/",
        data={
            "username": username,
            "password": password,
        }
    )
    assert login_response.status_code == status.HTTP_200_OK

    expected_json_answer = None
    if fail_type == GetInfoFailType.NO_FAIL:
        expected_json_answer = {"username": username, "email": email}
        get_info_response = await client.get(
            url=f"{settings.api.prefix_v1}/me/",
        )
        assert get_info_response.status_code == status_code
        assert get_info_response.json() == expected_json_answer

    else:
        if fail_type == GetInfoFailType.NO_ACCESS_TOKEN:
            expected_json_answer = {"detail": "Token not found."}
            client.cookies.pop("access_token")
        elif fail_type == GetInfoFailType.INVALID_TOKEN:
            expected_json_answer = {"detail": "Invalid token."}
            client.cookies.update({"access_token": "abcde"})

        get_info_response = await client.get(
            url=f"{settings.api.prefix_v1}/me/",
        )
        assert get_info_response.status_code == status_code
        assert get_info_response.json() == expected_json_answer
