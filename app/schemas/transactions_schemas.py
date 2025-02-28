from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
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


class SSortParamsBase(BaseModel):
    sort_by: list[str] | None = None

    @model_validator(mode="after")
    def validate_sort_by(self):
        if self.sort_by:
            sort_by_copy = self.sort_by.copy()
            self.sort_by.clear()
            for field in sort_by_copy:
                if field.lstrip("-") in self.allowed_fields:
                    if field.startswith("-"):
                        field = f"-{field.lstrip("-")}"
                    self.sort_by.append(field)
        return self


class STransactionsSortParams(SSortParamsBase):
    allowed_fields: dict = STransactionResponse.model_fields


class SortParam(BaseModel):
    order_by: str
    order_direction: Literal["asc", "desc"]


class SAmountRange(BaseModel):
    min_amount: int | None = Field(None, ge=0)
    max_amount: int | None = Field(None, ge=0)
