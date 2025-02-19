from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class SSpendingCategoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_name: str = Field(..., max_length=50)

    @field_validator("category_name")
    def validate_category_name(cls, value):
        return value.strip()


class SSpendingCategoryCreate(SSpendingCategoryBase):
    pass


class SSpendingCategoryOut(SSpendingCategoryBase):
    id: int
    user_id: int


class SSpendingCategoryUpdate(SSpendingCategoryBase):
    pass


class SpendingsOnDeleteActions(str, Enum):
    DELETE = "DELETE"
    TO_DEFAULT = "TO_DEFAULT"
    TO_EXISTS_CAT = "TO_EXISTS_CATEGORY"
    TO_NEW_CAT = "TO_NEW_CATEGORY"
