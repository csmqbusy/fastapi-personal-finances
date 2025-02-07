import pytest

from app.services.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


@pytest.mark.parametrize(
    "payload",
    [
        {"sub": "etoo"},
    ]
)
def test_create_access_token(
    payload: dict,
):
    token = create_access_token(payload)
    assert token is not None
    assert isinstance(token, str)

    decoded_payload = decode_access_token(token)
    assert decoded_payload is not None
    assert decoded_payload["sub"] == payload["sub"]


@pytest.mark.parametrize(
    "password",
    [
        "qwerty",
    ]
)
def test_hash_password(
    password: str,
):
    hashed_password = hash_password(password)
    assert hashed_password is not None
    assert verify_password(password, hashed_password)
