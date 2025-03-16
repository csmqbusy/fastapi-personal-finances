from datetime import date

import factory
from factory.faker import faker

from app.models import UserModel, SavingGoalsModel
from app.schemas.saving_goals_schemas import (
    GoalStatus,
    SSavingGoalUpdatePartial,
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

    name = fake.text(max_nb_chars=20)
    description = fake.text(max_nb_chars=100)
    current_amount = fake.pyint(min_value=0, max_value=1000)
    target_amount = fake.pyint(min_value=1001, max_value=100000)
    start_date = fake.date_between_dates(date(2020, 1, 1), date(2020, 12, 31))
    target_date = fake.date_between_dates(date(2021, 1, 1), date(2021, 12, 31))
