from datetime import datetime
from typing import Optional, Literal

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
)

from app.models import SpendingsModel


class SSpendingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: int = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=100)
    date: datetime | None


class SSpendingWithCategory(SSpendingBase):
    category_name: Optional[str] = Field(None, max_length=50)


class SSpendingCreate(SSpendingWithCategory):
    pass


class SSpendingResponse(SSpendingWithCategory):
    date: datetime
    id: int


class SSpendingCreateInDB(SSpendingBase):
    user_id: int
    category_id: int


class SSpendingUpdatePartial(BaseModel):
    amount: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=100)
    date: datetime | None
    category_name: Optional[str] = Field(None, max_length=50)


class SSpendingUpdatePartialInDB(BaseModel):
    amount: Optional[int] = None
    description: Optional[str] = Field(None, max_length=100)
    date: datetime | None


class STransactionsQueryParams(BaseModel):
    user_id: int | None = None
    category_id: int | None = None
    category_name: str | None = None


class STransactionsSortParams(BaseModel):
    sort_by: Optional[list[str]] = None

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
