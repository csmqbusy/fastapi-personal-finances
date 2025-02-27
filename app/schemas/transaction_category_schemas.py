from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class STransactionCategoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_name: str = Field(..., min_length=1, max_length=50)

    @field_validator("category_name")
    def validate_category_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("category_name cannot be empty")
        return value


class STransactionCategoryCreate(STransactionCategoryBase):
    pass


class STransactionCategoryOut(STransactionCategoryBase):
    id: int
    user_id: int


class STransactionCategoryUpdate(STransactionCategoryBase):
    pass


class TransactionsOnDeleteActions(StrEnum):
    DELETE = "DELETE"
    TO_DEFAULT = "TO_DEFAULT"
    TO_EXISTS_CAT = "TO_EXISTS_CATEGORY"
    TO_NEW_CAT = "TO_NEW_CATEGORY"


class SCategoryQueryParams(BaseModel):
    category_id: int | None = None
    category_name: str | None = None
