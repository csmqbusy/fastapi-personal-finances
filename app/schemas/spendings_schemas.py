from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class SSpendingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: int
    description: Optional[str] = Field(None, max_length=100)


class SSpendingWithCategory(SSpendingBase):
    category_name: Optional[str] = Field(None, max_length=50)


class SSpendingIn(SSpendingWithCategory):
    pass


class SSpendingOut(SSpendingWithCategory):
    date: datetime
    id: int


class SSpendingCreate(SSpendingBase):
    category_id: int
    user_id: int
