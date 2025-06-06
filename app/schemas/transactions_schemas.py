from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.schemas.common_schemas import SSortParamsBase


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

    @model_validator(mode="after")
    def microseconds_remove(self):
        if self.date:
            self.date = self.date.replace(microsecond=0)
        return self


class STransactionCreateInDB(STransactionBase):
    user_id: int
    category_id: int


class STransactionUpdatePartial(BaseModel):
    amount: int | None = Field(None, gt=0)
    description: str | None = Field(None, max_length=100)
    date: datetime | None = None
    category_name: str | None = Field(None, max_length=50)


class STransactionUpdatePartialInDB(BaseModel):
    amount: int | None = None
    description: str | None = Field(None, max_length=100)
    date: datetime | None


class STransactionsSortParams(SSortParamsBase):
    allowed_fields: dict = STransactionResponse.model_fields


class STransactionsSummary(BaseModel):
    category_name: str = Field(..., max_length=50)
    amount: int = Field(..., gt=0)


class BasePeriodTransactionsSummary(BaseModel):
    total_amount: int
    summary: list[STransactionsSummary]


class MonthTransactionsSummary(BasePeriodTransactionsSummary):
    month_number: int


class MonthTransactionsSummaryCSV(BaseModel):
    month_number: int
    category_name: str
    amount: int
    total_amount: int


class DayTransactionsSummary(BasePeriodTransactionsSummary):
    day_number: int


class DayTransactionsSummaryCSV(BaseModel):
    day_number: int
    category_name: str
    amount: int
    total_amount: int
