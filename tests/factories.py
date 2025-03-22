from datetime import date, datetime

import factory
from factory import LazyFunction
from factory.faker import faker

from app.models import (
    SavingGoalsModel,
    SpendingsModel,
    UserModel,
    UsersSpendingCategoriesModel,
)
from app.schemas.saving_goals_schemas import (
    GoalStatus,
    SSavingGoalUpdatePartial,
)
from app.schemas.transaction_category_schemas import STransactionCategoryUpdate
from app.schemas.transactions_schemas import (
    STransactionCreate,
    STransactionsSummary,
    STransactionUpdatePartial,
)
from app.services.auth_service import hash_password

fake = faker.Faker()


class UserFactory(factory.Factory):
    class Meta:
        model = UserModel

    username = factory.Sequence(lambda n: "user%s" % n)
    password = factory.LazyAttribute(lambda _: hash_password("password"))
    email = factory.LazyAttribute(lambda o: "%s@example.org" % o.username)
    active = True


class SavingGoalFactory(factory.Factory):
    class Meta:
        model = SavingGoalsModel

    name = factory.Sequence(lambda n: "Saving Goal %s" % n)
    description = factory.Sequence(lambda n: "sg description %s" % n)
    target_amount = 10000
    current_amount = 100
    target_date = date(2050, 12, 31)
    start_date = date.today()
    end_date = None
    status = GoalStatus.IN_PROGRESS
    user_id = None


class SavingGoalUpdateFactory(factory.Factory):
    class Meta:
        model = SSavingGoalUpdatePartial

    name = LazyFunction(lambda: fake.text(max_nb_chars=20))
    description = LazyFunction(lambda: fake.text(max_nb_chars=100))
    current_amount = LazyFunction(lambda: fake.pyint(min_value=0, max_value=1000))
    target_amount = LazyFunction(
        lambda: fake.pyint(min_value=1001, max_value=100000)
    )
    start_date = LazyFunction(
        lambda: fake.date_between_dates(date(2020, 1, 1), date(2020, 12, 31))
    )
    target_date = LazyFunction(
        lambda: fake.date_between_dates(date(2021, 1, 1), date(2021, 12, 31))
    )


class UsersSpendingCategoriesFactory(factory.Factory):
    class Meta:
        model = UsersSpendingCategoriesModel

    category_name = LazyFunction(lambda: fake.text(max_nb_chars=20))
    user_id = None


class TransactionCategoryUpdateFactory(factory.Factory):
    class Meta:
        model = STransactionCategoryUpdate

    category_name = LazyFunction(lambda: fake.text(max_nb_chars=50))


class SpendingsFactory(factory.Factory):
    class Meta:
        model = SpendingsModel

    amount = LazyFunction(lambda: fake.pyint(min_value=0, max_value=10000))
    description = LazyFunction(lambda: fake.text(max_nb_chars=30))
    date = LazyFunction(
        lambda: fake.date_time_between_dates(
            date(2020, 1, 1), date(2028, 12, 31)
        ).replace(microsecond=0)
    )
    user_id = None
    category_id = None


class STransactionCreateFactory(factory.Factory):
    class Meta:
        model = STransactionCreate

    amount = LazyFunction(lambda: fake.pyint(min_value=0, max_value=10000))
    description = LazyFunction(lambda: fake.text(max_nb_chars=30))
    date = LazyFunction(
        lambda: fake.date_time_between_dates(
            date(2020, 1, 1), date(2028, 12, 31)
        ).replace(microsecond=0)
    )
    category_name: str | None = None


class STransactionUpdateFactory(factory.Factory):
    class Meta:
        model = STransactionUpdatePartial

    amount: int | None = LazyFunction(
        lambda: fake.pyint(min_value=0, max_value=10000)
    )
    description: str | None = LazyFunction(lambda: fake.text(max_nb_chars=30))
    date: datetime | None = LazyFunction(
        lambda: fake.date_time_between_dates(
            date(2020, 1, 1), date(2028, 12, 31)
        ).replace(microsecond=0)
    )
    category_name: str | None = None


class STransactionsSummaryFactory(factory.Factory):
    class Meta:
        model = STransactionsSummary

    category_name = LazyFunction(lambda: fake.text(max_nb_chars=10))
    amount = LazyFunction(lambda: fake.pyint(min_value=1, max_value=10000))
