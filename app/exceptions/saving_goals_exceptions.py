class GoalsException(Exception):
    pass


class GoalNotFound(GoalsException):
    pass


class GoalCurrentAmountInvalid(GoalsException):
    pass
