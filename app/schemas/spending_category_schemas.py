from pydantic import BaseModel, Field, ConfigDict


class SSpendingCategoryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=50)


class SSpendingCategoryIn(SSpendingCategoryBase):
    pass


class SSpendingCategoryOut(SSpendingCategoryBase):
    id: int
