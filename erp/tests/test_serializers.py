from datetime import date, timedelta

from django.contrib.auth.models import User, Group
from django.test import TestCase

from rest_framework.exceptions import ValidationError, ErrorDetail

from erp import factories as erp_factories
from erp import models as erp_models
from erp import serializers as erp_serializers


class SubscriberSerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # we need it existing for every subscriber
        Group.objects.create(name='Subscribers')

    def setUp(self):
        self.sub = erp_factories.SubscriberFactory()

    def test_deserialize_valid_subscriber(self):
        sub = {
            "address_number_and_street": "1, rue de la Paix",
            "address_zipcode": "75001",
            "iban": "FR7630056009271234567890182",
            "user": {
                "email": "john.doe@test.co",
                "first_name": "John",
                "last_name": "Doe",
                "password": "fakepwdd"
            }
        }

        serializer = erp_serializers.SubscriberSerializer(data=sub)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertTrue(bool(erp_models.Subscriber.objects.get(user__username='john.doe@test.co')))
        sub = erp_models.Subscriber.objects.get(user__username='john.doe@test.co')

        self.assertEqual(sub.subscription_date, date.today())
        self.assertFalse(sub.has_rent_issue)
        self.assertFalse(sub.received_warning)
        self.assertFalse(bool(sub.current_rentals))

    def test_deserialize_invalid_subscriber_missing_required_field(self):
        """Subscriber with address_zipcode missing
        """
        sub = {
            "address_number_and_street": "1, rue de la Paix",
            "iban": "FR7630056009271234567890182",
            "user": {
                "email": "john.doe@test.co",
                "first_name": "John",
                "last_name": "Doe",
                "password": "fakepwdd"
            }
        }
        serializer = erp_serializers.SubscriberSerializer(data=sub)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        # can't do errors.keys() because drf relies on heavy odict (ordered dict)
        # sets are required to get a flat, standard python data type
        self.assertEqual(set(serializer.errors), set(['address_zipcode']))
        # error message from the serializer:
        # ValidationError({'address_zipcode': [ErrorDetail(string='This field is required.', code='required')]})
        # in the response of the endpoint:
        # {"address_zipcode": ["This field is required."]}

    def test_deserialize_invalid_sub_missing_required_field_in_related_model(self):
        """Job done with a custom validate() method in the Subscriber serializer"""
        sub = {
            "address_number_and_street": "1, rue de la Paix",
            "address_zipcode": "75001",
            "iban": "FR7630056009271234567890182",
            "user": {
                "email": "john.doe@test.co",
                "last_name": "Doe",
                "password": "fakepwdd"
            }
        }
        serializer = erp_serializers.SubscriberSerializer(data=sub)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        self.assertEqual(
            serializer.errors['non_field_errors'],
            [ErrorDetail(string='The user first_name is missing', code='invalid')]
        )

    def test_deserialize_invalid_subscriber_not_matching_fieldtype_requirements(self):
        """Subscriber with misformed email address (DRF's job)
        """
        sub = {
            "address_number_and_street": "1, rue de la Paix",
            "address_zipcode": "75001",
            "iban": "FR7630056009271234567890182",
            "user": {
                "email": "john.doe",
                "first_name": "John",
                "last_name": "Doe",
                "password": "fakepwdd"
            }
        }
        sub_ser = erp_serializers.SubscriberSerializer(data=sub)
        with self.assertRaises(ValidationError):
            sub_ser.is_valid(raise_exception=True)
        self.assertEqual(set(sub_ser.errors['user']), set(['email']))

    def test_serialize_subscriber(self):
        sub = self.sub

        serializer = erp_serializers.SubscriberSerializer(sub)
        self.assertTrue('address_number_and_street' in set(serializer.data))
        self.assertTrue('first_name' in serializer.data['user'].keys())

    # not really useful test, somehow testing DRF's many=True flag
    def test_serialize_subscriber_list(self):
        subs = erp_factories.SubscriberFactory.create_batch(5)

        serializer = erp_serializers.SubscriberSerializer(subs, many=True)
        self.assertEqual(len(serializer.data), 5)

    def test_valid_update_subscribers(self):
        sub = self.sub

        sub_update = {
            "address_number_and_street": "2, rue de la Paix"
        }
        
        serializer = erp_serializers.SubscriberSerializer(instance=sub, data=sub_update, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(sub.address_number_and_street, "2, rue de la Paix")

    def test_invalid_update_subscribers(self):
        """Read_only fields don't raise an error when trying to update them.
        """
        sub = erp_factories.SubscriberFactory(
            user__username='lin.liu@test.co'
        )

        sub_update = {
            "user": {"username": "Zoro"}
        }

        serializer = erp_serializers.SubscriberSerializer(instance=sub, data=sub_update, partial=True)
        serializer.is_valid(raise_exception=True)
        new_sub = serializer.save()

        self.assertEqual(new_sub.user.username, 'lin.liu@test.co')


class LibrarianSerializerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.librarians_group = Group.objects.create(name='Librarians')
        cls.managers_group = Group.objects.create(name='Managers')

    def test_deserialize_valid_librarian(self):
        librarian = {
            "is_manager": False,
            "user": {
                "email": "lin.liu@library.com",
                "first_name": "Lin",
                "last_name": "Liu",
                "password": "fakepwdd",
            }
        }

        serializer = erp_serializers.LibrarianSerializer(data=librarian)
        serializer.is_valid(raise_exception=True)
        lib = serializer.save()

        self.assertEqual(lib.user.groups.first(), self.librarians_group)
        self.assertEqual(lib.user.username, 'lliu')
        self.assertTrue(lib.user.is_active)

    def test_deserialize_invalid_librarian_missing_required_field(self):
        librarian = {
            "user": {
                "email": "lin.liu@library.com",
                "first_name": "Lin",
                "last_name": "Liu",
                "password": "fakepwdd",
            }
        }

        serializer = erp_serializers.LibrarianSerializer(data=librarian)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        self.assertEqual(
            serializer.errors,
            {'is_manager': [ErrorDetail(string='This field is required.', code='required')]}
        )

    def test_deserialize_invalid_librarian_missing_required_field_in_related_model(self):
        librarian = {
            "is_manager": False,
            "user": {
                "email": "lin.liu@library.com",
                "first_name": "Lin",
                "password": "fakepwdd",
            }
        }

        serializer = erp_serializers.LibrarianSerializer(data=librarian)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
        self.assertEqual(
            serializer.errors,
            {'non_field_errors': [ErrorDetail(string='The user last_name is missing', code='invalid')]}
        )

    def test_deserialize_librarian_with_complex_name(self):
        librarian = {
            "is_manager": False,
            "user": {
                "email": "lin.liu@library.com",
                "first_name": "Jean-Léonard",
                "last_name": "de la Fiérière",
                "password": "fakepwdd",
            }
        }

        serializer = erp_serializers.LibrarianSerializer(data=librarian)
        serializer.is_valid(raise_exception=True)
        lib = serializer.save()

        self.assertEqual(lib.user.username, 'jdelafieriere')
        self.assertEqual(lib.user.groups.first(), self.librarians_group)

    def test_deserialize_valid_manager(self):
        librarian = {
            "is_manager": True,
            "user": {
                "email": "lin.liu@library.com",
                "first_name": "Lin",
                "last_name": "Liu",
                "password": "fakepwdd",
            }
        }

        serializer = erp_serializers.LibrarianSerializer(data=librarian)
        serializer.is_valid(raise_exception=True)
        lib = serializer.save()

        self.assertEqual(lib.user.groups.first(), self.managers_group)
        self.assertEqual(lib.user.username, 'lliu')
        self.assertTrue(lib.user.is_active)

    def test_serialize_librarian(self):
        sub = erp_factories.StandardLibrarianFactory()

        sub_ser = erp_serializers.LibrarianSerializer(sub)
        self.assertTrue('is_manager' in set(sub_ser.data))
        self.assertTrue('first_name' in sub_ser.data['user'].keys())

    def test_valid_update_librarian(self):
        lib = erp_factories.StandardLibrarianFactory(
            user__first_name='Jack',
            user__last_name='Credit'
        )

        lib_update = {"user": {"last_name": "Cash"}}

        lib_ser = erp_serializers.LibrarianSerializer(
            instance=lib,
            data=lib_update,
            partial=True
        )
        lib_ser.is_valid(raise_exception=True)
        lib = lib_ser.save()

        self.assertEqual(lib.user.last_name, 'Cash')
        self.assertEqual(lib.user.first_name, 'Jack')

    def test_invalid_update_librarian(self):
        """read_only fields are just ignored"""
        lib = erp_factories.StandardLibrarianFactory(
            user__username='JackCash'
        )

        lib_update = {'user': {'username': 'JC'}}
        lib_ser = erp_serializers.LibrarianSerializer(
            instance=lib,
            data=lib_update,
            partial=True
        )
        lib_ser.is_valid(raise_exception=True)
        lib = lib_ser.save()

        self.assertEqual(lib.user.username, 'JackCash')


class GenericBookSerializerTest(TestCase):
    """
    These tests span 2 serializers: GenericBookSerializerWrite
    and GenericBookSerializerRead which are used in the views
    depending whether we are writing and reading.
    """
    @classmethod
    def setUpTestData(cls):
        cls.thoreau = erp_factories.AuthorFactory()
        cls.essay = erp_factories.GenreFactory()
        cls.walden = erp_factories.GenericBookFactory()

    def test_deserialize_valid_genericbook(self):
        gbook = {
            'title': 'Walden, or Life in the Woods',
            'author': self.thoreau.id, # by default, ModelSerializers read id as int
            'genre': self.essay.id,
            'publication_year': 1854,
        }

        gbook_ser = erp_serializers.GenericBookSerializerWrite(data=gbook)
        gbook_ser.is_valid(raise_exception=True)
        gbook = gbook_ser.save()

        self.assertTrue(isinstance(gbook, erp_models.GenericBook))
        self.assertEqual(gbook.author, self.thoreau)

    def test_deserialize_invalid_genericbook_missing_required_field(self):
        gbook = {
            'author': self.thoreau.id, # by default, ModelSerializers read id as int
            'genre': self.essay.id,
            'publication_year': 1854,
        }

        gbook_ser = erp_serializers.GenericBookSerializerWrite(data=gbook)
        with self.assertRaises(ValidationError):
            gbook_ser.is_valid(raise_exception=True)
        self.assertEqual(
            gbook_ser.errors,
            {'title': [ErrorDetail(string='This field is required.', code='required')]}
        )

    def test_deserialize_invalid_genericbook_missing_relation_id(self):
        """Note that a missing relation id is considered
           as a missing required field.
        """
        gbook = {
            'title': 'Walden, or Life in the Woods',
            'author': self.thoreau.id, # by default, ModelSerializers read id as int
            'publication_year': 1854,
        }

        gbook_ser = erp_serializers.GenericBookSerializerWrite(data=gbook)
        with self.assertRaises(ValidationError):
            gbook_ser.is_valid(raise_exception=True)
        self.assertEqual(
            gbook_ser.errors,
            {'genre': [ErrorDetail(string='This field is required.', code='required')]}
        )

    def test_serialize_genericbook(self):
        gbook = self.walden

        gbook_ser = erp_serializers.GenericBookSerializerRead(gbook)
        self.assertEqual(gbook_ser.data['publication_year'], 1854)
        # the related object Author is not an ID, because
        # a StringRelatedField is used to represent it (__str__ is self.name)
        self.assertEqual(gbook_ser.data['author'], 'Henry David Thoreau')

    def test_valid_update_genericbook(self):
        gbook = self.walden
        gbook_update = {'publication_year': 1860}

        gbook_ser = erp_serializers.GenericBookSerializerWrite(
            instance=gbook,
            data=gbook_update,
            partial=True
        )
        gbook_ser.is_valid(raise_exception=True)
        gbook_ser.save()

        self.assertTrue(isinstance(gbook, erp_models.GenericBook))
        self.assertEqual(gbook.title, 'Walden, or Life in the Woods')
        self.assertEqual(gbook.publication_year, 1860)

    def test_invalid_update_genericbook_with_low_level_protection(self):
        """
        Not possible to remove 'id' from writable serializers, otherwise
        no reference to perform updates.

        Yet when trying to update fields that are protected at the model
        or DB-levels, like 'id', even though we don't receive validation
        errors (unlike Django, DRF doesn't split form validation between
        the forms and the models they rely on - clean()) the update is
        not performed, as the last assert of gbook.id proves it.
        """
        gbook = self.walden
        gbook_id = gbook.id
        gbook_update = {'id': 1000}

        gbook_ser = erp_serializers.GenericBookSerializerWrite(
            instance=gbook,
            data=gbook_update,
            partial=True
        )
        self.assertTrue(gbook_ser.is_valid(raise_exception=True))
        gbook = gbook_ser.save() # or: gbook_ser.save(), then gbook.refresh_from_db()
        self.assertEqual(gbook.id, gbook_id)


class BookSerializerTest(TestCase):
    """
    This testcase doesn't repeat the test performed above with invalid
    objects to deserialize and update, it's little redundant and concern
    mainly DRF's serializers inner work.
    """
    @classmethod
    def setUpTestData(cls):
        cls.gbook = erp_factories.GenericBookFactory(
            title='Zero to One',
        )

    def test_deserialize_valid_book(self):
        """A serializer raises the `required` error only if
         1) the field is required by the model,
         2) the field received the DRF argument `required=True`
        """
        book = {
            'generic_book_id': self.gbook.id,
        }

        book_ser = erp_serializers.BookSerializer(data=book)
        book_ser.is_valid(raise_exception=True)
        book = book_ser.save()

        self.assertTrue(isinstance(book, erp_models.Book))
        self.assertEqual(book.status, 'MAINTENANCE')
        self.assertEqual(book.generic_book.title, 'Zero to One')

    def test_deserialize_invalid_book_with_invalid_choice(self):
        book = {
            'generic_book_id': self.gbook.id,
            'status': 'FREE',
        }

        book_ser = erp_serializers.BookSerializer(data=book)
        with self.assertRaises(ValidationError):
            book_ser.is_valid(raise_exception=True)
        self.assertEqual(
            book_ser.errors,
            {'status': [ErrorDetail(string='"FREE" is not a valid choice.', code='invalid_choice')]}
        )

    def test_serialize_valid_book(self):
        book = erp_factories.ActiveBookFactory()

        book_ser = erp_serializers.BookSerializer(book)
        self.assertTrue('joined_library_on' in book_ser.data.keys())
        self.assertEqual(book_ser.data['status'], 'ACTIVE')
