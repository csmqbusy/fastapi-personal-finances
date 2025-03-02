from datetime import date
from enum import Enum
from typing import Self

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
)


class GoalStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class SSavingGoalBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=100)
    current_amount: int = Field(..., ge=0)
    target_amount: int = Field(..., gt=0)
    start_date: date | None = None
    target_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.start_date > self.target_date:
            raise ValueError("start_date cannot be later than target_date")
        return self


class SSavingGoalCreate(SSavingGoalBase):
    pass


class SSavingGoalCreateInDB(SSavingGoalBase):
    user_id: int
    status: GoalStatus = GoalStatus.IN_PROGRESS


class SSavingGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    current_amount: int
    target_amount: int
    start_date: date | None = None
    target_date: date
    end_date: date | None = None
    status: GoalStatus


class SSavingGoalUpdatePartial(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    description: str | None = Field(None, max_length=100)
    current_amount: int | None = None
    target_amount: int | None = Field(None, gt=0)
    start_date: date | None = None
    target_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.start_date and self.target_date:
            if self.start_date > self.target_date:
                raise ValueError("start_date cannot be later than target_date")
        return self
