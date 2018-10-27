from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User, Group

import factory

from . import models as erp_models


# Groups

class BaseGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)


class ManagerGroupFactory(BaseGroupFactory):
    name = 'Managers'


class LibrarianGroupFactory(BaseGroupFactory):
    name = 'Librarians'


class SubscriberGroupFactory(BaseGroupFactory):
    name = 'Subscribers'


# Users

class LibrarianUserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    # factory.Sequence is a solution against IntegrityError in tests
    # when calling several times the same factory, directly or indirectly (via SubFactories)
    username = factory.Sequence(lambda n: 'emile.litre%d' % n)
    password = make_password('fakepwdd') # pretty rough, not for production
    email = factory.Sequence(lambda n: 'emile.litre%d@library.com' % n)
    first_name = 'Emile'
    last_name = factory.Sequence(lambda n: 'Littré%d' % n)

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        group = LibrarianGroupFactory.create()
        self.groups.add(group)


class ManagerUserFactory(LibrarianUserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        group = ManagerGroupFactory()
        self.groups.add(group)


# don't overwrite this factory to create a custom user
# it won't work, the password won't get hashed
class SubscriberUserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User
        # django_get_or_create = ('username',)
        # it's a bad idea to use django_get_or_create because we can't overwrite a property
        # when calling an existing object
        # Example
        # s = SubscriberUserFactory()
        # s.password => 'fakepwdd'
        # s2 = SubscriberUserFactory(password='bar')
        # s2.password => 'fakewpdd' # not what I want!
        # so either delete the object after each test (or flush the DB)
        # or use create new object each time with factory.Sequence(lambda n: 'foo - %d' % n)
        # to avoid IntegrityError which happens otherwise when we try to create similar objects

    username = factory.Sequence(lambda n: 'lin.liu%d@test.co' % n)
    password = make_password('fakepwdd')  # pretty rough, not for production
    email = factory.Sequence(lambda n: 'lin.liu%d@test.co' % n)
    first_name = 'Lin'
    last_name = factory.Sequence(lambda n: 'Liu - %d' % n)

    # important to use the signature from the doc, else don't work
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        sub_group = SubscriberGroupFactory.create()
        self.groups.add(sub_group)


# Library profiles: librarians, managers, subscribers


class StandardLibrarianFactory(factory.DjangoModelFactory):
    class Meta:
        model = erp_models.Librarian

    user = factory.SubFactory(LibrarianUserFactory)
    is_manager = False


class ManagerLibrarianFactory(StandardLibrarianFactory):
    user = factory.SubFactory(ManagerUserFactory)
    is_manager = True


class SubscriberFactory(factory.DjangoModelFactory):
    """
    This factory represents the nominal case of an active subscriber.

    For the subscriber to be active,
    make sure subscription_date + SUBSCRIPTION_DAYS_LENGTH < today
    """
    class Meta:
        model = erp_models.Subscriber

    user = factory.SubFactory(SubscriberUserFactory)
    address_number_and_street = factory.Sequence(lambda n: '%d, rue de la Paix' % n)
    address_zipcode = '75001'
    iban = 'FR7630056009271234567890182'


# Book related resources

class AuthorFactory(factory.DjangoModelFactory):
    class Meta:
        model = erp_models.Author
        django_get_or_create = ('name',)
        # get_or_create is ok here as we won't try to modify the value of the name

    name = 'Henry David Thoreau'


class GenreFactory(factory.DjangoModelFactory):
    class Meta:
        model = erp_models.Genre
        django_get_or_create = ('name',)

    name = 'Essay'


class GenericBookFactory(factory.DjangoModelFactory):
    class Meta:
        model = erp_models.GenericBook
        django_get_or_create = ('title',)
        # get_or_create is ok here as we won't try to modify the GenericBook as there's little logic involving books
        # BUT whenever they are some modifications implied with GenericBook and the tests fails, chances are the culprit
        # is here. Then, remove get_or_create and go for sequences

    title = 'Walden, or Life in the Woods'
    author = factory.SubFactory(AuthorFactory)
    genre = factory.SubFactory(GenreFactory)
    publication_year = 1854


class BaseBookFactory(factory.DjangoModelFactory):
    """Don't use this one directly, rather one of its subclasses"""
    class Meta:
        model = erp_models.Book

    # no need to do sth with a Sequence here as the id is an AutoField (id auto-incrementing)
    generic_book = factory.SubFactory(GenericBookFactory)


class AvailableBookFactory(BaseBookFactory):
    status = 'AVAILABLE'


class RentBookFactory(BaseBookFactory):
    status = 'RENT'


class RetiredBookFactory(BaseBookFactory):
    joined_library_on = date(2000, 1, 1)
    left_library_on = date(2010, 1, 1)
    left_library_cause = 'WORN'
    status = 'RETIRED'


# Rentals

class BaseRentalFactory(factory.DjangoModelFactory):
    class Meta:
        model = erp_models.Rental

    # TODO create a subscriber and use its related user
    # but doesn't work because FactoryBoy is lazy, evaluate only at the very end
    # may be possible with a factory User, including a RelatedFactory on Subscriber
    # to make up for the reverse ForeignKey
    # But for now, it's better to create rental by hand with a subscriber and book
    # created just before
    user = factory.SubFactory(SubscriberUserFactory)
    book = factory.SubFactory(RentBookFactory)


class NewRentalFactory(BaseRentalFactory):
    rent_on = date.today()


class TightRentalFactory(BaseRentalFactory):
    rent_on = date.today() - timedelta(days=(settings.MAX_RENT_DAYS - 1))


class DueRentalFactory(BaseRentalFactory):
    rent_on = date.today() - timedelta(days=(settings.MAX_RENT_DAYS + 1))
    late = True


class ReturnedOnTimeRentalFactory(BaseRentalFactory):
    rent_on = date.today() - timedelta(days=100)
    returned_on = date.today() - timedelta(days=90)


class ReturnedLateRentalFactory(BaseRentalFactory):
    rent_on = date.today() - timedelta(days=100)
    returned_on = date.today() - timedelta(days=50)
    late = True
