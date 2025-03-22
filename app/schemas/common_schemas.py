from datetime import date, datetime
from typing import Literal, Self

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


class SDateRange(BaseModel):
    start: date | None = None
    end: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start and self.end:
            if self.start > self.end:
                raise InvalidDateRange
        return self


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


class SortParam(BaseModel):
    order_by: str
    order_direction: Literal["asc", "desc"]
