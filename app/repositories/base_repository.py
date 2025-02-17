from typing import Type, TypeVar, Generic, Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def add(
        self,
        session: AsyncSession,
        obj_in: dict,
    ) -> T:
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def get(
        self,
        session: AsyncSession,
        id_: Any,
    ) -> T | None:
        return await session.get(self.model, id_)

    async def get_all(
        self,
        session: AsyncSession,
        params: dict,
        order_by: str | None = None,
        order_direction: Literal["asc", "desc"] = "asc",
    ) -> list[T]:
        query = select(self.model).filter_by(**params)

        if order_by:
            if order_direction == "asc":
                query = query.order_by(getattr(self.model, order_by).asc())
            else:
                query = query.order_by(getattr(self.model, order_by).desc())

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_one_by_filter(
        self,
        session: AsyncSession,
        params: dict,
    ) -> T | None:
        query = select(self.model).filter_by(**params)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self,
        session: AsyncSession,
        object_id: int,
        params: dict,
    ) -> T | None:
        object_from_db = await session.get(self.model, object_id)
        for key, value in params.items():
            setattr(object_from_db, key, value)
        await session.commit()
        await session.refresh(object_from_db)
        return object_from_db

    async def delete(
        self,
        session: AsyncSession,
        id_: Any,
    ) -> None:
        db_obj = await self.get(session, id_)
        if db_obj:
            await session.delete(db_obj)
            await session.commit()
