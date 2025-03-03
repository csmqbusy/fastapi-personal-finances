from fastapi import HTTPException, status


class TransactionNotFoundError(HTTPException):
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


class MissingCategoryError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Either category_id or category_name must be provided.",
        )


class CategoryNameNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter the name of the category for transactions "
                   "moving or select the DEFAULT mode.",
        )


class CannotDeleteDefaultCategoryError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete the default category.",
        )


class InvalidDataRangeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The start date must be less than the end date.",
        )


class CategoryInfoError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Send information about categories in only one format: "
                   "either category_ids or category_names.",
        )


class GoalNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saving goal not found.",
        )


class GoalCurrentAmountError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saving goal current amount cannot be less than 0.",
        )
