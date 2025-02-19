from typing import Type, Iterable

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.categories_exceptions import (
    CategoryAlreadyExists,
    CategoryNotFound,
    CategoryNameNotFound,
    CannotDeleteDefaultCategory,
)
from app.schemas.spending_category_schemas import (
    SSpendingCategoryUpdate,
    SpendingsOnDeleteActions,
)


class BaseCategoriesService:
    def __init__(
        self,
        category_repo,
        transaction_repo,
        default_category_name: str,
        out_schema: Type[BaseModel],
    ):
        self.category_repo = category_repo
        self.transaction_repo = transaction_repo
        self.default_category_name = default_category_name
        self.out_schema = out_schema

    async def get_category(
        self,
        user_id: int,
        category_name: str,
        session: AsyncSession,
    ):
        category = await self.category_repo.get_category(
            session=session,
            user_id=user_id,
            category_name=category_name,
        )
        return category

    async def get_default_category(
        self,
        user_id: int,
        session: AsyncSession,
    ):
        category = await self.get_category(
            user_id,
            self.default_category_name,
            session,
        )
        return category

    async def add_category_to_db(
        self,
        user_id: int,
        category_name: str,
        session: AsyncSession,
    ):
        category = await self.get_category(user_id, category_name, session)
        if category:
            raise CategoryAlreadyExists
        category = await self.category_repo.add(
            session,
            dict(user_id=user_id, category_name=category_name),
        )
        return self.out_schema.model_validate(category)

    async def get_user_categories(
        self,
        user_id: int,
        session: AsyncSession,
    ):
        user_categories = await self.category_repo.get_all(
            session,
            dict(user_id=user_id),
        )
        return user_categories

    async def add_user_default_category(
        self,
        user_id: int,
        session: AsyncSession,
    ) -> None:
        await self.add_category_to_db(
            user_id,
            self.default_category_name,
            session,
        )

    async def update_category(
        self,
        category_name: str,
        user_id: int,
        category_update_obj: SSpendingCategoryUpdate,
        session: AsyncSession,
    ):
        category = await self.get_category(user_id, category_name, session)
        if not category:
            raise CategoryNotFound

        new_category = await self.get_category(
            user_id, category_update_obj.category_name, session)
        if new_category:
            raise CategoryAlreadyExists

        updated_category = await self.category_repo.update(
            session=session,
            object_id=category.id,
            params=dict(category_name=category_update_obj.category_name),
        )
        return self.out_schema.model_validate(updated_category)

    async def delete_category(
        self,
        category_name: str,
        user_id: int,
        transactions_actions: SpendingsOnDeleteActions,
        new_category_name: str | None,
        session: AsyncSession,
    ):
        if category_name.capitalize() == self.default_category_name:
            raise CannotDeleteDefaultCategory

        category_for_delete = await self.get_category(
            user_id, category_name, session)
        if category_for_delete is None:
            raise CategoryNotFound

        transactions = await self.transaction_repo.get_all(
            session, dict(category_id=category_for_delete.id, user_id=user_id))

        if transactions_actions == SpendingsOnDeleteActions.DELETE:
            for spending in transactions:
                await self.transaction_repo.delete(session, spending.id)
        elif transactions_actions == SpendingsOnDeleteActions.TO_DEFAULT:
            default_category = await self.get_default_category(user_id, session)
            await self.change_transactions_category(
                transactions,
                default_category.id,
                session,
            )
        else:
            if new_category_name is None:
                raise CategoryNameNotFound
            if transactions_actions == SpendingsOnDeleteActions.TO_NEW_CAT:
                await self.add_category_to_db(
                    user_id,
                    new_category_name,
                    session,
                )
            category = await self.get_category(
                user_id,
                new_category_name,
                session,
            )
            if category is None:
                raise CategoryNotFound

            await self.change_transactions_category(
                transactions,
                category.id,
                session,
            )
        await self.category_repo.delete(session, category_for_delete.id)

    async def change_transactions_category(
        self,
        transactions: Iterable,
        new_category_id: int,
        session: AsyncSession,
    ):
        repo = self.transaction_repo

        for t in transactions:
            transaction_in_db = await repo.get_transaction_with_category(
                session,
                t.id,
            )
            transaction_in_db.category_id = new_category_id

        await session.commit()
