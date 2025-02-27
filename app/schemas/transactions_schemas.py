from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
)


class STransactionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: int = Field(..., gt=0)
    description: str | None = Field(None, max_length=100)
    date: datetime | None = None


class STransactionCreate(STransactionBase):
    category_name: str | None = Field(None, max_length=50)


class STransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: int
    category_name: str | None = None
    description: str | None
    date: datetime
    id: int


class STransactionCreateInDB(STransactionBase):
    user_id: int
    category_id: int


class STransactionUpdatePartial(BaseModel):
    amount: int | None = Field(None, gt=0)
    description: str | None = Field(None, max_length=100)
    date: datetime | None
    category_name: str | None = Field(None, max_length=50)


class STransactionUpdatePartialInDB(BaseModel):
    amount: int | None = None
    description: str | None = Field(None, max_length=100)
    date: datetime | None


class SCategoryQueryParams(BaseModel):
    category_id: int | None = None
    category_name: str | None = None


class STransactionsSortParams(BaseModel):
    sort_by: list[str] | None = None

    @field_validator("sort_by")
    def validate_sort_by(
        cls,
        value: list[str],
    ) -> list[str]:
        if not value:
            return value

        allowed_fields = STransactionResponse.model_fields

        value_copy = value.copy()
        value.clear()
        for field in value_copy:
            if field.lstrip("-") in allowed_fields:
                if field.startswith("-"):
                    field = f"-{field.lstrip("-")}"
                value.append(field)
        return value


class SortParam(BaseModel):
    order_by: str
    order_direction: Literal["asc", "desc"]


class SAmountRange(BaseModel):
    min_amount: int | None = Field(None, ge=0)
    max_amount: int | None = Field(None, ge=0)
