from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
)


class SSpendingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: int
    description: Optional[str] = Field(None, max_length=100)

    @field_validator("amount")
    def validate_amount(cls, value):
        if value < 0:
            raise ValueError("Price cannot be negative")
        return value


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
    amount: Optional[int] = None
    description: Optional[str] = Field(None, max_length=100)
    category_name: Optional[str] = Field(None, max_length=50)

    @field_validator("amount")
    def validate_amount(cls, value):
        if value and value < 0:
            raise ValueError("Price cannot be negative")
        return value


class SSpendingUpdatePartialInDB(BaseModel):
    amount: Optional[int] = None
    description: Optional[str] = Field(None, max_length=100)
