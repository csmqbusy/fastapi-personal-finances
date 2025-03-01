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
    amount: int = Field(..., gt=0)
    target_date: date
    start_date: date | None = None
    end_date: date


class SSavingGoalCreate(SSavingGoalBase):
    pass
