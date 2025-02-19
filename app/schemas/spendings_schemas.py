from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
)

from app.models import SpendingsModel


class STransactionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: int = Field(..., gt=0)
    description: str | None = Field(None, max_length=100)
    date: datetime | None


class STransactionWithCategory(STransactionBase):
    category_name: str | None = Field(None, max_length=50)


class STransactionCreate(STransactionWithCategory):
    pass


class STransactionResponse(STransactionWithCategory):
    date: datetime
    id: int


class STransactionCreateInDB(STransactionBase):
    user_id: int
    category_id: int


class SSpendingUpdatePartial(BaseModel):
    amount: int | None = Field(None, gt=0)
    description: str | None = Field(None, max_length=100)
    date: datetime | None
    category_name: str | None = Field(None, max_length=50)


class SSpendingUpdatePartialInDB(BaseModel):
    amount: int | None = None
    description: str | None = Field(None, max_length=100)
    date: datetime | None


class STransactionsQueryParams(BaseModel):
    user_id: int | None = None
    category_id: int | None = None
    category_name: str | None = None


class STransactionsSortParams(BaseModel):
    sort_by: list[str] | None = None

    @field_validator("sort_by")
    def validate_sort_by(cls, value: list[str]):
        if not value:
            return value

        allowed_fields = [a for a in dir(SpendingsModel) if not a.startswith("_")]

        value_copy = value.copy()
        value.clear()
        for field in value_copy:
            if field.lstrip("-") in allowed_fields:
                value.append(field)
        return value


class SortParam(BaseModel):
    order_by: str
    order_direction: Literal["asc", "desc"]
