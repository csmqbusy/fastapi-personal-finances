class TransactionException(Exception):
    pass


class TransactionNotFound(TransactionException):
    pass


class InvalidDateRange(TransactionException):
    pass
