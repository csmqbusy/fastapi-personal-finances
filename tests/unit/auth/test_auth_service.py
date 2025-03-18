import pytest

from app.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    validate_username,
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


@pytest.mark.parametrize(
    "username, result",
    [
        ("qwerty", True),
        ("12345", True),
        ("1_2_3", True),
        ("_Q_W_E_", True),
        ("q" * 2, False),
        ("q" * 25, False),
        ("", False),
        ("qwe rty", False),
        ("@werty", False),
    ]
)
def test_validate_username(
    username: str,
    result: bool,
):
    assert validate_username(username) == result
