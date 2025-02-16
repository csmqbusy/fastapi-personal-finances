from pydantic import BaseModel


class SPagination(BaseModel):
    page: int
    page_size: int
