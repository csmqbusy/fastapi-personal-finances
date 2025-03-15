import factory

from app.models import UserModel
from app.services.auth_service import hash_password


class UserFactory(factory.Factory):
    class Meta:
        model = UserModel

    username = factory.Sequence(lambda n: 'user%s' % n)
    password = factory.LazyAttribute(lambda _: hash_password("password"))
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)
    active = True
