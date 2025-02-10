from pydantic import BaseModel, ConfigDict


class SUserSpendingCategories(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    category_id: int
