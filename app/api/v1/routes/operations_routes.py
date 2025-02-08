from fastapi import APIRouter

router = APIRouter()


@router.post("/add_spending")
def add_spending():
    ...
