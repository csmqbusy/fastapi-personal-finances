from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)


class SSpendingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: int = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=100)


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
    category_name: Optional[str] = Field(None, max_length=50)


class SSpendingUpdatePartialInDB(BaseModel):
    amount: Optional[int] = None
    description: Optional[str] = Field(None, max_length=100)


class STransactionsQueryParams(BaseModel):
    user_id: int | None = None
    category_id: int | None = None
    category_name: str | None = None
