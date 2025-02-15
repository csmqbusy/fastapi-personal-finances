from fastapi import HTTPException, status


class SpendingNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Spending not found.",
        )


class CategoryAlreadyExistsError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a category with that name.",
        )


class CategoryNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Create this category before performing operations on it.",
        )


class CategoryNameNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please enter the name of the category for transactions "
                   "moving or select the DEFAULT mode.",
        )


class CannotDeleteDefaultCategoryError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You cannot delete the default category.",
        )
