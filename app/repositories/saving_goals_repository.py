from app.models import SavingGoalsModel
from app.repositories.base_repository import BaseRepository


class SavingGoalsRepository(BaseRepository[SavingGoalsModel]):
    def __init__(self):
        super().__init__(SavingGoalsModel)


saving_goals_repo = SavingGoalsRepository()
