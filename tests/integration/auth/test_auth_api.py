import pytest
from factory.faker import faker
from httpx import AsyncClient
from starlette import status

from app.core.config import settings
from app.models import UserModel
from tests.factories import UserFactory

fake = faker.Faker()


@pytest.mark.asyncio
async def test_sign_up_user__success(client: AsyncClient):
    user = UserFactory()
    response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": user.username,
            "password": user.password.decode(),
            "email": user.email,
        },
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_sign_up_user__same_username_or_email(client: AsyncClient):
    user = UserFactory()
    await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": user.username,
            "password": user.password.decode(),
            "email": user.email,
        },
    )

    response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": user.username,
            "password": user.password.decode(),
            "email": fake.email(),
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_up/",
        json={
            "username": fake.user_name(),
            "password": user.password.decode(),
            "email": user.email,
        },
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_login__success(client: AsyncClient, user: UserModel):
    assert client.cookies.get("access_token") is None
    response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_in/",
        data={
            "username": user.username,
            "password": "password",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert client.cookies.get("access_token")


@pytest.mark.asyncio
async def test_login__wrong_username_or_password(
    client: AsyncClient,
    user: UserModel,
):
    assert client.cookies.get("access_token") is None
    response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_in/",
        data={
            "username": fake.user_name(),
            "password": "password",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    response = await client.post(
        url=f"{settings.api.prefix_v1}/sign_in/",
        data={
            "username": user.username,
            "password": "wrong_password",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert client.cookies.get("access_token") is None


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_user: UserModel):
    assert client.cookies.get("access_token")

    logout_response = await client.post(
        url=f"{settings.api.prefix_v1}/logout/",
    )
    assert logout_response.status_code == status.HTTP_200_OK
    assert client.cookies.get("access_token") is None


@pytest.mark.asyncio
async def test_auth_user_get_info__success(
    client: AsyncClient,
    auth_user: UserModel,
):
    get_info_response = await client.get(f"{settings.api.prefix_v1}/me/")
    assert get_info_response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_auth_user_get_info__no_access_token(
    client: AsyncClient,
    auth_user: UserModel,
):
    client.cookies.pop("access_token")
    get_info_response = await client.get(f"{settings.api.prefix_v1}/me/")
    assert get_info_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_auth_user_get_info__invalid_token(
    client: AsyncClient,
    auth_user: UserModel,
):
    client.cookies.update({"access_token": "abcde"})
    get_info_response = await client.get(f"{settings.api.prefix_v1}/me/")
    assert get_info_response.status_code == status.HTTP_401_UNAUTHORIZED
