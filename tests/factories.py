import factory

from app.models import UserModel


class UserFactory(factory.Factory):
    class Meta:
        model = UserModel

    username = factory.Sequence(lambda n: 'user%s' % n)
    password = "password".encode()
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)
    active = True
