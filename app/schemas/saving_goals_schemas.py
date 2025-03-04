from datetime import date
from enum import Enum
from typing import Self

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
    field_validator,
)

from app.schemas.common_schemas import SSortParamsBase


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

    @field_validator("name")
    def validate_name(cls, v):
        return v.strip()

    @field_validator("description")
    def validate_description(cls, v):
        if v:
            v = v.strip()
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.start_date and self.start_date > self.target_date:
            raise ValueError("start_date cannot be later than target_date")
        return self


class SSavingGoalCreate(SSavingGoalBase):
    pass


class SSavingGoalCreateInDB(SSavingGoalBase):
    user_id: int
    status: GoalStatus = GoalStatus.IN_PROGRESS
    end_date: date | None = None


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
    current_amount: int | None = Field(None, ge=0)
    target_amount: int | None = Field(None, gt=0)
    start_date: date | None = None
    target_date: date | None = None

    @field_validator("name")
    def validate_name(cls, v):
        if v:
            v = v.strip()
        return v

    @field_validator("description")
    def validate_description(cls, v):
        if v:
            v = v.strip()
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.start_date and self.target_date:
            if self.start_date > self.target_date:
                raise ValueError("start_date cannot be later than target_date")
        if self.current_amount and self.target_amount:
            if self.current_amount > self.target_amount:
                raise ValueError(
                    "current_amount cannot be greater than target_amount"
                )
        return self


class SSavingGoalProgress(BaseModel):
    current_amount: int
    target_amount: int
    rest_amount: int
    percentage_progress: int
    days_left: int
    expected_daily_payment: int


class SGoalsSortParams(SSortParamsBase):
    allowed_fields: dict = SSavingGoalResponse.model_fields
