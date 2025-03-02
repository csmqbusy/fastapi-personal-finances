from datetime import date
from enum import Enum
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    WithJsonSchema,
)


class GoalStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class SSavingGoalBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=50)
    description: Annotated[
        str | None,
        WithJsonSchema({'examples': [None]}),
    ] = Field(None, max_length=100)
    current_amount: int = Field(..., ge=0)
    target_amount: Annotated[
        int,
        WithJsonSchema({'examples': [1000]}),
    ] = Field(..., gt=0)
    start_date: date | None = None
    target_date: date


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
