from datetime import datetime

from pydantic import BaseModel, Field


class SSpendingBase(BaseModel):
    amount: float
    description: str | None = Field(None, max_length=100)
    category_name: str | None = Field(None, max_length=50)


class SSpendingIn(SSpendingBase):
    pass


class SSpendingOut(SSpendingBase):
    date: datetime
