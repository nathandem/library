from datetime import date, timedelta

from django.contrib.auth.models import User, Group
from django.test import TestCase

from rest_framework.exceptions import ValidationError, ErrorDetail

from erp import factories as erp_factories
from erp import models as erp_models
from erp import serializers as erp_serializers


class SubscriberSerializerTest(TestCase):
    def setUp(self):
        # add the Subscribers group to the test methods if delete setUp
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

    def test_update_subscribers_read_only_field(self):
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
