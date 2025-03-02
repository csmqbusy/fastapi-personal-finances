from app.repositories.saving_goals_repository import saving_goals_repo
from app.schemas.saving_goals_schemas import SSavingGoalCreate


class SavingGoalsService:
    def __init__(self):
        self.repo = saving_goals_repo


saving_goals_service = SavingGoalsService()
