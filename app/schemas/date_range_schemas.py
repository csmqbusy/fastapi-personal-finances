from datetime import date
from typing import Self

from pydantic import BaseModel, model_validator

from app.exceptions.transaction_exceptions import InvalidDateRange


    start: date | None = None
    end: date | None = None
class SDatetimeRange(BaseModel):

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start and self.end:
            if self.start > self.end:
                raise InvalidDateRange
        return self
