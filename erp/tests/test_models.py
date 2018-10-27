from datetime import date, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError # could do a test with ProtectedError
from django.test import TestCase

from freezegun import freeze_time

from erp import factories as erp_factories
from erp import models as erp_models


# date helpers
today = date.today()
one_year_ago = date.today() - timedelta(days=365)


class SubscriberModelTest(TestCase):
    def test_subscription_validity(self):
        day_before_end_sub = date.today() - timedelta(days=settings.SUBSCRIPTION_DAYS_LENGTH - 1)
        day_end_sub = date.today() - timedelta(days=settings.SUBSCRIPTION_DAYS_LENGTH)

        new_sub = erp_factories.SubscriberFactory(
            subscription_date=date.today()
        )
        self.assertTrue(new_sub.valid_subscription)

        with freeze_time(day_before_end_sub):
            tight_sub = erp_factories.SubscriberFactory()
        self.assertTrue(tight_sub.valid_subscription)

        with freeze_time(day_end_sub):
            inactive_sub = erp_factories.SubscriberFactory()
        self.assertFalse(inactive_sub.valid_subscription)

    def test_issues_with_subscriber(self):
        sub = erp_factories.SubscriberFactory()
        self.assertFalse(sub.has_rent_issue)
        self.assertFalse(sub.received_warning)
        self.assertTrue(sub.can_rent)

        sub.received_warning = True
        self.assertFalse(sub.has_rent_issue)
        self.assertTrue(sub.can_rent)

        sub.has_rent_issue = True
        self.assertFalse(sub.can_rent)

    def test_books_related_properties(self):
        sub_with_no_book = erp_factories.SubscriberFactory()
        self.assertEqual(sub_with_no_book.current_rentals.count(), 0)
        self.assertEqual(list(sub_with_no_book.current_bookings), [])
        self.assertTrue(sub_with_no_book.can_rent)

        sub_with_books = erp_factories.SubscriberFactory()
        # create_batch() returns a list of objects, not queryset just like create() does with an object
        books = erp_factories.RentBookFactory.create_batch(settings.MAX_RENT_BOOKS - 1)
        rentals = [erp_models.Rental.objects.create(
            user=sub_with_books.user,
            book=book,
        ) for book in books]
        self.assertEqual(sub_with_books.current_rentals.count(), 2)
        self.assertEqual(list(sub_with_books.current_rentals), rentals)
        self.assertEqual(list(sub_with_books.current_bookings), [])
        self.assertTrue(sub_with_books.can_rent)

        another_book = erp_factories.RentBookFactory()
        another_rental = erp_models.Rental.objects.create(
            user=sub_with_books.user,
            book=another_book,
        )
        rentals.append(another_rental)
        self.assertEqual(sub_with_books.current_rentals.count(), 3)
        self.assertEqual(list(sub_with_books.current_rentals), rentals)
        self.assertEqual(list(sub_with_books.current_bookings), [])
        self.assertFalse(sub_with_books.can_rent)


class BookModelTest(TestCase):
    def test_joined_date(self):
        new_book = erp_factories.AvailableBookFactory()
        self.assertEqual(new_book.joined_library_on, date.today())

        with freeze_time(one_year_ago):
            one_year_old_book = erp_factories.AvailableBookFactory.create()
        self.assertEqual(one_year_old_book.joined_library_on, one_year_ago)

    def test_book_retire(self):
        properly_retired_book = erp_factories.RetiredBookFactory()
        self.assertEqual(properly_retired_book.status, 'RETIRED')
        self.assertTrue(bool(properly_retired_book.left_library_on))
        self.assertTrue(bool(properly_retired_book.left_library_cause))

        badly_retired_book = erp_factories.AvailableBookFactory()
        with self.assertRaises(ValidationError) as cm:
            badly_retired_book.status = 'RETIRED'
            badly_retired_book.save() # no saving, but badly_retired_book.status is still 'RETIRED' locally
        # important to test that we raised the correct ValidationError exception, and not another one
        self.assertEqual(
            cm.exception.message,
            "A book can't be retired without both left_library_on and left_library_cause filled",
        )

        badly_retired_book = erp_factories.AvailableBookFactory()
        with self.assertRaises(ValidationError) as cm:
            badly_retired_book.left_library_on = today
            badly_retired_book.save()
        self.assertEqual(
            cm.exception.message,
            "A book can't left the library without a cause",
        )

        badly_retired_book = erp_factories.AvailableBookFactory()
        with self.assertRaises(ValidationError) as cm:
            badly_retired_book.status = 'RETIRED'
            badly_retired_book.left_library_on = today
            badly_retired_book.save()
        self.assertEqual(
            cm.exception.message,
            "A book can't left the library without a cause",
        )

    def test_book_rental_property(self):
        available_book = erp_factories.AvailableBookFactory()
        self.assertIsNone(available_book.current_rental)

        # opti: would be better to use one rental factory for that
        sub = erp_factories.SubscriberFactory()
        rent_book = erp_factories.RentBookFactory()
        rental = erp_models.Rental.objects.create(
            user=sub.user,
            book=rent_book,
        )
        self.assertEqual(rent_book.current_rental, rental)


class BookingModelTest(TestCase):
    pass # to come
