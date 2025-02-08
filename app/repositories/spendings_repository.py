from app.models import SpendingsModel
from app.repositories.base_repository import BaseRepository


class SpendingsRepository(BaseRepository[SpendingsModel]):
    def __init__(self):
        super().__init__(SpendingsModel)


spendings_repo = SpendingsRepository()
