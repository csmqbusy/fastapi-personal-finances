class CategoriesException(Exception):
    pass


class CategoryAlreadyExists(CategoriesException):
    pass


class CategoryNotFound(CategoriesException):
    pass


class CategoryNameNotFound(CategoriesException):
    pass
