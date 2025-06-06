from datetime import date
from enum import Enum

from sqlalchemy import Enum as alch_Enum
from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base
from app.models.mixins import IdIntPKMixin
from app.schemas.saving_goals_schemas import GoalStatus


class SavingGoalsModel(IdIntPKMixin, Base):
    __tablename__ = "saving_goals"

    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(100), nullable=True)
    target_amount: Mapped[int]
    current_amount: Mapped[int]
    target_date: Mapped[date]
    start_date: Mapped[date] = mapped_column(server_default=text("CURRENT_DATE"))
    end_date: Mapped[date] = mapped_column(nullable=True)
    status: Mapped[Enum] = mapped_column(alch_Enum(GoalStatus))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
