"""
Just call the views and test the response objects.
(the view is a black box)
Test the components of the view in unit tests, like test_serializers and test_utils.

Tests to write:
for the GET of RentBook
1) check subscriber who can rent (no book rent),
  can indeed rent and has the correct response
2) check subscriber who cannot rent,
  cannot rent indeed and has the correct response
3) check subscriber who can rent (1 book rent),
  can indeed rent and has the correct response (2 allowed)

do tests for the POST of RentBook, the POST of ReturnBook,
the GET and POST of BookGenericBook
"""

from django.test import TestCase

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate

from erp import models as erp_models
from erp import factories as erp_factories


class RentBookViewTest(TestCase):
    def test_renting(self):

        book = erp_factories.ActiveBookFactory()
        sub = erp_factories.SubscriberFactory()

        request_factory = APIRequestFactory()
        request = request_factory.get('/api/rent/1/')
