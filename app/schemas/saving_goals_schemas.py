from datetime import date
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)


class GoalStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class SSavingGoalBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=100)
    target_amount: int = Field(..., gt=0)
    current_amount: int = Field(..., ge=0)
    target_date: date
    start_date: date | None = None
    end_date: date


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
