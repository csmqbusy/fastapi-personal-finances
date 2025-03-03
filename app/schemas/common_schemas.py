from pydantic import BaseModel, Field


class SAmountRange(BaseModel):
    min_amount: int | None = Field(None, ge=0)
    max_amount: int | None = Field(None, ge=0)


class SPagination(BaseModel):
    page: int
    page_size: int
