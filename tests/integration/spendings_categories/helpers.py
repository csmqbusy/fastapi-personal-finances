from random import randint

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_repo
from app.schemas.user_schemas import SUserSignUp


async def add_mock_user(db_session: AsyncSession, username: str) -> None:
    mock_email = f"mock{randint(1, 100_000_000)}{randint(1, 100_000_000)}@i.ai"
    user_schema = SUserSignUp(
        username=username,
        password=b"qwerty",
        email=mock_email,  # type: ignore
    )
    await user_repo.add(db_session, user_schema.model_dump())
