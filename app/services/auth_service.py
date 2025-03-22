import re
from datetime import UTC, datetime

import bcrypt
import jwt

from app.core.config import settings


def create_access_token(
    payload: dict,
    private_key: str = settings.auth.private_key_path.read_text(),
    algorithm: str = settings.auth.algorithm,
) -> str:
    to_encode = payload.copy()
    iat = datetime.now(UTC).timestamp()
    expire = (iat + settings.auth.access_token_expires_sec)
    to_encode.update(
        iat=iat,
        exp=expire,
    )
    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=private_key,
        algorithm=algorithm,
    )
    return encoded_jwt


def decode_access_token(
    token: str | bytes,
    public_key: str = settings.auth.public_key_path.read_text(),
    algorithm: str = settings.auth.algorithm,
) -> dict:
    decoded = jwt.decode(
        jwt=token,
        key=public_key,
        algorithms=[algorithm]
    )
    return decoded


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def verify_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password)


def validate_username(username: str) -> bool:
    valid_pattern = re.compile(r"^[a-zA-Z0-9_]{3,24}$")
    return bool(valid_pattern.match(username))
