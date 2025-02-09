from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SSpendingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: float
    description: str | None = Field(None, max_length=100)
    category_name: str | None = Field(None, max_length=50)


class SSpendingIn(SSpendingBase):
    pass


class SSpendingOut(SSpendingBase):
    date: datetime
