from typing import Generic, TypeVar, Type

from pydantic import BaseModel


T = TypeVar('T')


class BaseCategoriesService(Generic[T]):
    def __init__(
        self,
        category_repo,
        default_category_name: str,
        out_schema: Type[BaseModel],
    ):
        self.category_repo = category_repo
        self.default_category_name = default_category_name
        self.out_schema = out_schema
