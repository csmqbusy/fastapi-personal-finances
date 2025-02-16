class CategoriesException(Exception):
    pass


class CategoryAlreadyExists(CategoriesException):
    pass


class CategoryNotFound(CategoriesException):
    pass


class MissingCategory(CategoriesException):
    pass


class CategoryNameNotFound(CategoriesException):
    pass


class CannotDeleteDefaultCategory(CategoriesException):
    pass
