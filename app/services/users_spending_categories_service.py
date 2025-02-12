from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_spend_cat_repo


async def get_user_categories(
    user_id: int,
    session: AsyncSession,
):
    user_categories = await user_spend_cat_repo.get_all_by_filter(
        session,
        dict(user_id=user_id),
    )
    return user_categories
