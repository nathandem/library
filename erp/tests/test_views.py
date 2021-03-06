"""
Approch for testing views:
Just call the views and test the response objects.
Treat the view is a black box. Its custom component should be tested
in dedicated unit tests, like test_serializers and test_utils.

Scope:
I don't test the resource-centric endpoints as they are all the same
(only a small risk of typo), testing them is super-repetitive (if I
come across a lib for this go, else no test).
I only test the business logic intensive/process-centric ones.
See urls.py for the difference.
"""
from datetime import date, timedelta

from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from freezegun import freeze_time
from knox.models import AuthToken

from erp import models as erp_models
from erp import factories as erp_factories


# time helpers
today = date.today()
one_year_ahead = date.today() + timedelta(days=365)
rental_due_for = date.today() + timedelta(days=settings.MAX_RENT_DAYS)


class ResourceViewTest(APITestCase):
    """
    Test just a few endpoints to see how DRF behave.
    For invalid auth, see test_permissions
    """
    @classmethod
    def setUpTestData(cls):
        cls.mgr = erp_factories.ManagerLibrarianFactory()
        cls.mgr_token = AuthToken.objects.create(cls.mgr.user)
        cls.lib = erp_factories.StandardLibrarianFactory()
        cls.lib_token = AuthToken.objects.create(cls.lib.user)
        cls.client = APIClient()

    def test_librarian_endpoint_create_valid(self):
        res = self.client.post(
            path='/api/librarians/',
            data={'is_manager': True,
                  'user': {
                      'first_name': 'Lin',
                      'last_name': 'Liu',
                      'email': 'lin.liu@library.co',
                      'password': 'fakepwdd',
                  }},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.mgr_token,
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(erp_models.Librarian.objects.filter(user__username='lliu').exists())

    def test_librarian_endpoint_create_invalid(self):
        res = self.client.post(
            path='/api/librarians/',
            data={'is_manager': True,
                  'user': {
                      'first_name': 'Lin',
                      'email': 'lin.liu@library.co',
                      'password': 'fakepwdd',
                  }},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.mgr_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(
            res,
            # unlike other errors, DRF sends more than 'detail' for ValidationError
            '{"non_field_errors":["The user last_name is missing"]}',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_librarian_endpoint_read(self):
        res = self.client.get(
            path='/api/librarians/',
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.mgr_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 2)
        self.assertEqual(res.data['next'], None)
        self.assertEqual(res.data['previous'], None)

    def test_librarian_endpoint_get_non_existing_object(self):
        """
        The result of this test determines the result of all
        tests involving a 404 error in a view with DRF.
        """
        res = self.client.get(
            path='/api/librarians/%s/' % 1000000,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.mgr_token,
        )

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertContains(
            res,
            '{"detail":"Not found."}',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_subscriber_detail_get_response(self):
        sub = erp_factories.SubscriberFactory()
        erp_factories.AvailableBookFactory()

        res = self.client.get(
            path='/api/subscribers/%s/' % sub.id,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue('current_rentals' in res.data)
        self.assertTrue('current_bookings' in res.data)


class RentViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lib = erp_factories.StandardLibrarianFactory()
        cls.lib_token = AuthToken.objects.create(cls.lib.user)
        cls.client = APIClient()

    def setUp(self):
        self.sub = erp_factories.SubscriberFactory()
        self.books = erp_factories.AvailableBookFactory.create_batch(5)

    def test_check_endpoint__no_sub_pk(self):
        """
        When hitting an endpoint which doesn't exist, client gets a 404.
        The request is not generated by DRF, but Django. That's why the
        response is not in JSON, but HTML.
        """
        res = self.client.get(
            path='/api/rent/',
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertContains(
            res,
            '<h1>Not Found</h1><p>The requested URL /api/rent/ was not found on this server.</p>',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_check_sub_can_rent(self):
        # check if sub can rent, no active rental and no issue
        res = self.client.get(
            path='/api/rent/%s/' % self.sub.pk,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['can_rent'], True)
        self.assertContains(res, '"nb_books_allowed":3')
        self.assertContains(res, '"current_rentals":null')
        self.assertContains(res, '"issues":null')

        # check if sub can rent, 1 active rental and no issue
        erp_models.Rental.objects.create(
            user=self.sub.user,
            book=self.books[0],
        )
        res = self.client.get(
            path='/api/rent/%s/' % self.sub.pk,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(res, '"can_rent":true')
        self.assertContains(res, '"nb_books_allowed":2')
        self.assertEqual(len(res.data['current_rentals']), 1)
        self.assertContains(res, '"issues":null')

    def test_check_sub_can_rent__max_rents_books_no_issue(self):
        for book in self.books[:3]:
            erp_models.Rental.objects.create(
                user=self.sub.user,
                book=book,
            )

        res = self.client.get(
            path='/api/rent/%s/' % self.sub.pk,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(res, '"can_rent":false', status_code=400)
        self.assertContains(res, '"nb_books_allowed":0', status_code=400)
        self.assertEqual(len(res.data['current_rentals']), 3)
        self.assertEqual(
            res.data['issues'],
            [{"type": "Max number of books rent already reached."}]
        )

    @freeze_time(one_year_ahead)
    def test_check_sub_can_rent__subscription_expired(self):
        res = self.client.get(
            path='/api/rent/%s/' % self.sub.pk,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['can_rent'], False)
        self.assertEqual(res.data.get('nb_books_allowed'), 0)
        self.assertEqual(res.data['current_rentals'], None)
        self.assertEqual(
            res.data['issues'],
            [{"type": "The subscriber's subscription is over."}]
        )

    def test_check_sub_can_rent__has_issue(self):
        # sub doesn't have any active rental
        sub = self.sub
        sub.has_issue = True
        sub.save()

        res = self.client.get(
            path='/api/rent/%s/' % self.sub.pk,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['can_rent'], False)
        self.assertEqual(res.data.get('nb_books_allowed'), 0)
        self.assertEqual(res.data['current_rentals'], None)
        self.assertEqual(
            res.data['issues'],
            [{"type": "The subscriber has rent issues."}]
        )

        # sub has one active rental
        book = erp_factories.AvailableBookFactory()
        erp_models.Rental.objects.create(user=sub.user, book=book)

        res = self.client.get(
            path='/api/rent/%s/' % self.sub.pk,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['can_rent'], False)
        self.assertEqual(res.data.get('nb_books_allowed'), 0)
        self.assertEqual(
            res.data['current_rentals'],
            [{"title": book.generic_book.title,
              "date_of_return": rental_due_for,}]
        )
        self.assertEqual(
            res.data['issues'],
            [{"type": "The subscriber has rent issues."}]
        )

    def test_check_sub_can_rent__non_existing_book(self):
        res = self.client.get(
            path='/api/rent/%s/' % 1000000,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertContains(
            res,
            '{"detail":"Not found."}',
            status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_rent_books(self):
        """
        POST request done after the check done with the GET request
        on same endpoint.
        """
        sub = self.sub

        # rent one book, okay
        book1 = self.books[0]
        self.assertEqual(book1.status, 'AVAILABLE')
        res = self.client.post(
            path='/api/rent/%s/' % self.sub.pk,
            data={'book_id': book1.pk},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['book__generic_book__title'], self.books[0].generic_book.title)
        self.assertEqual(res.data['due_for'], rental_due_for)

        self.assertTrue(erp_models.Rental.objects.get(book=book1))
        book1.refresh_from_db()
        self.assertEqual(book1.status, 'RENT')
        # no refresh from DB, as the property is dynamic
        self.assertEqual(sub.current_rentals.count(), 1)

        # rent two more books, still okay
        for i in range(1, 3):
            res = self.client.post(
                path='/api/rent/%s/' % self.sub.pk,
                data={'book_id': self.books[i].pk},
                format='json',
                HTTP_AUTHORIZATION='Token %s' % self.lib_token,
            )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['book__generic_book__title'], self.books[0].generic_book.title)
        self.assertEqual(res.data['due_for'], rental_due_for)

        # try renting one more book, not okay this time
        res = self.client.post(
            path='/api/rent/%s/' % self.sub.pk,
            data={'book_id': self.books[3].pk},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['can_rent'], False)
        self.assertEqual(len(res.data['current_rentals']), 3)
        self.assertContains(
            res,
            '"issues":[{"type":"Max number of books rent already reached."}]',
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(sub.current_rentals.count(), 3)

    def test_rent_a_book__no_ref(self):
        res = self.client.post(
            path='/api/rent/%s/' % self.sub.pk,
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['detail'], "No book_id was provided.")


class ReturnViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lib = erp_factories.StandardLibrarianFactory()
        cls.lib_token = AuthToken.objects.create(cls.lib.user)
        cls.client = APIClient()

    def setUp(self):
        self.sub = erp_factories.SubscriberFactory()
        self.books = erp_factories.AvailableBookFactory.create_batch(5)

    def test_return_a_book_valid(self):
        sub = self.sub
        book = self.books[0]

        rental = erp_models.Rental.objects.create(
            user=sub.user,
            book=book,
        )
        book.status = 'RENT'
        book.save()

        # return book on time
        res = self.client.post(
            path='/api/return/%s/' % sub.pk,
            data={"book_id": book.id},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data.get('success'),
            "{} was correctly returned.".format(book.generic_book.title)
        )

        self.assertEqual(sub.current_rentals.count(), 0)
        book.refresh_from_db()
        self.assertEqual(book.status, 'AVAILABLE')
        rental.refresh_from_db()
        self.assertEqual(rental.returned_on, today)
        self.assertEqual(rental.late, False)

    def test_return_book_from_someone_else(self):
        sub1 = self.sub
        sub2 = erp_factories.SubscriberFactory()
        book = self.books[0]

        rental = erp_models.Rental.objects.create(
            user=sub1.user,
            book=book,
        )
        book.status = 'RENT'
        book.save()

        res = self.client.post(
            path='/api/return/%s/' % sub2.pk,
            data={"book_id": book.id},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            res.data['detail'],
            "You can't return a book that you didn't rent yourself."
        )


class ReserveGenericBookViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.lib = erp_factories.StandardLibrarianFactory()
        cls.lib_token = AuthToken.objects.create(cls.lib.user)
        cls.client = APIClient()

    def setUp(self):
        self.sub = erp_factories.SubscriberFactory()
        self.gbook = erp_factories.GenericBookFactory()

    def test_book_available_copy_genericbook(self):
        gbook = self.gbook
        book = erp_factories.AvailableBookFactory()

        res = self.client.post(
            path='/api/reserve/%s/' % self.sub.id,
            data={'genericbook_id': gbook.id},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(
            response=res,
            text="The book {gbook} ref {book_id} is booked for you, until {date_end_booking}".format(
                gbook=gbook,
                book_id=book.id,
                date_end_booking=date.today() + timedelta(days=settings.MAX_BOOKING_DAYS)
            )
        )

    def test_book_non_available_copy_genericbook(self):
        gbook = self.gbook
        book = erp_factories.RentBookFactory()

        res = self.client.post(
            path='/api/reserve/%s/' % self.sub.id,
            data={'genericbook_id': gbook.id},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(
            response=res,
            text="The book {gbook} is booked for you. Unfortunately, no book is available is the library right now. We'll email you as soon as we have a copy of it.".format(
                gbook=gbook,
            )
        )

    def test_reserve_non_existing_book(self):
        res = self.client.post(
            path='/api/reserve/%s/' % self.sub.id,
            data={'genericbook_id': 1000000},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_reserve_bad_payload(self):
        res = self.client.post(
            path='/api/reserve/%s/' % self.sub.id,
            data={'gbook_id': self.gbook.id},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(
            response=res,
            text='{"detail":"No genericbook_id was provided."}',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_reserve_cant_book(self):
        sub = erp_factories.SubscriberFactory(has_issue=True)

        res = self.client.post(
            path='/api/reserve/%s/' % sub.id,
            data={'genericbook_id': self.gbook.id},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % self.lib_token,
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(
            response=res,
            text="Sorry, you can't reserve books. Check your status to find out why.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
