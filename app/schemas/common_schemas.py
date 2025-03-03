from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.exceptions.transaction_exceptions import InvalidDateRange


class SAmountRange(BaseModel):
    min_amount: int | None = Field(None, ge=0)
    max_amount: int | None = Field(None, ge=0)


class SPagination(BaseModel):
    page: int
    page_size: int


class SDatetimeRange(BaseModel):
    start: datetime | None = None
    end: datetime | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start and self.end:
            if self.start > self.end:
                raise InvalidDateRange
        return self
