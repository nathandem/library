"""
What do we need to cover for proper auth testing?

1) User management
Creation/update/deletion of users (subscribers and librarians).
It's already taken care of with both serializer tests (for the underlying)
and view tests (for the integration tests). So no more here.

2) Authentication backend: knox
What to test?
- login (good, 1 or 2 bad)
- logout (good)
- logoutall

3) Permissions
Test the few group-based permissions.
At least, one case for working permission and one for not working.
"""

# 301: redirection

# 400: bad request
# 401: not successfully authenticated
# 403: successfully authenticated, but permission denied
# 405: method not allowed
# 415: unsupported media type

# response.status_code
# response.content = what is returned to the user
# response.cookies = cookies returned to the client
# response.template_name
# response.context

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from erp import factories as erp_factories


class KnoxViewTest(APITestCase):
    """
    Idea: make sure knox works as expected.
    A little redundant with the lib own tests (link below),
    but ensure that few feature I want work as expected.
    ref: https://github.com/James1345/django-rest-knox/blob/master/tests/tests.py
    """
    # warning: if django.test.TestCase is used,
    # self.client will revert to django.test.Client
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.lib = erp_factories.StandardLibrarianFactory()

    def test_login_valid_user(self):
        res = self.client.post(
            path='/api/login/',
            data={'username': self.lib.user.username,
                  # can't use the password from the user,
                  # it's hashed in the DB
                  'password': 'fakepwdd'},
            # important to specify 'json' (= 'application/json')
            # otherwise 'multipart/form-data' is picked by default for post requests
            # and django/DRF don't know what MIME parser to use
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(res, 'token')
        self.assertContains(res, 'user')

        lib_token = res.data['token']
        res = self.client.get(
            '/api/books/',
            HTTP_AUTHORIZATION='Token %s' % lib_token,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_login_existing_user_wrong_password(self):
        res = self.client.post(
            path='/api/login/',
            data={'username': self.lib.user.username,
                  'password': 'wrong_password'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(
            response=res,
            text='{"non_field_errors":["Unable to log in with provided credentials."]}',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_login_non_existing_user(self):
        res = self.client.post(
            path='/api/login/',
            data={'username': 'gost',
                  'password': 'gost_pwd'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertContains(
            response=res,
            text='{"non_field_errors":["Unable to log in with provided credentials."]}',
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_access_protected_views_without_auth_token(self):
        res = self.client.get(
            '/api/librarians/',
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertContains(
            response=res,
            text='{"detail":"Authentication credentials were not provided."}',
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    def test_logout(self):
        """Test that a user is logout on his current device"""
        res = self.client.post(
            path='/api/login/',
            data={'username': self.lib.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        lib_token = res.data['token']

        res = self.client.get(
            '/api/books/',
            HTTP_AUTHORIZATION='Token %s' % lib_token,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.post(
            path='/api/logout/',
            HTTP_AUTHORIZATION='Token %s' % lib_token,
            format='json',
        )
        self.assertEqual(res.status_code, 204)

        res = self.client.get(
            '/api/books/',
            HTTP_AUTHORIZATION='Token %s' % lib_token,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_full_logout(self):
        """Test that a given user is logout on all his connected devices"""
        # Get mobile token and use it to access one page
        log_mobile = self.client.post(
            path='/api/login/',
            data={'username': self.lib.user.username,
                  'password': 'fakepwdd'},
            format='json',
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
        )
        mobile_token = log_mobile.data['token']

        res = self.client.get(
            '/api/books/',
            HTTP_AUTHORIZATION='Token %s' % mobile_token,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Get dektop token and use it to access one page
        # is this enough to simulate 2 different devices?
        log_desktop = self.client.post(
            path='/api/login/',
            data={'username': self.lib.user.username,
                  'password': 'fakepwdd'},
            format='json',
            HTTP_USER_AGENT='Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0'
        )
        desktop_token = log_desktop.data['token']

        res = self.client.get(
            '/api/books/',
            HTTP_AUTHORIZATION='Token %s' % desktop_token,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # full logout using desktop_token
        res_logout = self.client.post(
            path='/api/logoutall/',
            HTTP_AUTHORIZATION='Token %s' % desktop_token,
            format='json',
        )
        self.assertEqual(res_logout.status_code, status.HTTP_204_NO_CONTENT)

        # test both desktop and mobile can't access the page
        res = self.client.get(
            '/api/books/',
            HTTP_AUTHORIZATION='Token %s' % desktop_token,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        res = self.client.get(
            '/api/books/',
            HTTP_AUTHORIZATION='Token %s' % mobile_token,
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionTest(APITestCase):
    """
    The idea here to test that the custom permissions work as expected.
    """
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()

        # all share the password 'fakepwdd'
        cls.sub = erp_factories.SubscriberFactory()
        cls.lib = erp_factories.StandardLibrarianFactory()
        cls.mgr = erp_factories.ManagerLibrarianFactory()

    def test_view_with_no_perm(self):
        res = self.client.post(
            path='/api/login/',
            data={'username': self.sub.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_failing_auth_no_token(self):
        res = self.client.get(
            path='/api/librarians/',
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertContains(
            res,
            '{"detail":"Authentication credentials were not provided."}',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    def test_mgr_perm_valid(self):
        res = self.client.post(
            path='/api/login/',
            data={'username': self.mgr.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        mgr_token = res.data['token']

        res = self.client.get(
            path='/api/librarians/',
            format='json',
            HTTP_AUTHORIZATION='Token %s' % mgr_token,
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_mgr_perm_view_invalid_perm_denied(self):
        """
        All or nothing permissions like the IsManager, testing one
        success case and one 403 (auth ok, perm ko) is enough.
        """
        res = self.client.post(
            path='/api/login/',
            data={'username': self.sub.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        sub_token = res.data.get('token')

        res = self.client.get(
            path='/api/librarians/',
            format='json',
            HTTP_AUTHORIZATION='Token %s' % sub_token,
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertContains(
            res,
            '{"detail":"You need to be a manager to perform this action"}',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_lib_perm_valid(self):
        res = self.client.post(
            path='/api/login/',
            data={'username': self.lib.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        lib_token = res.data.get('token')

        res = self.client.get(
            path='/api/subscribers/',
            format='json',
            HTTP_AUTHORIZATION='Token %s' % lib_token,
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_lib_perm_invalid_perm_denied(self):
        res = self.client.post(
            path='/api/login/',
            data={'username': self.sub.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        sub_token = res.data.get('token')

        res = self.client.get(
            path='/api/subscribers/',
            format='json',
            HTTP_AUTHORIZATION='Token %s' % sub_token,
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertContains(
            res,
            '{"detail":"You need to be a librarian to perform this action."}',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_sub_perm_valid(self):
        # TODO test booking endpoint here when ready
        res = self.client.post(
            path='/api/login/',
            data={'username': self.sub.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        sub_token = res.data['token']

    def test_sub_perm_invalid_perm_denied(self):
        pass # TODO

    def test_lib_or_sub_read_only_perm_valid_sub_read(self):
        res = self.client.post(
            path='/api/login/',
            data={'username': self.sub.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        sub_token = res.data['token']

        res = self.client.get(
            path='/api/generic_books/',
            format='json',
            HTTP_AUTHORIZATION='Token %s' % sub_token,
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_lib_or_sub_read_only_perm_invalid_not_auth(self):
        res = self.client.get(
            path='/api/generic_books/',
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertContains(
            res,
            '{"detail":"Authentication credentials were not provided."}',
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    def test_lib_or_sub_read_only_perm_valid_lib_modif(self):
        gbook = erp_factories.GenericBookFactory.create()
        self.assertNotEqual(gbook.title, 'Walking')

        res = self.client.post(
            path='/api/login/',
            data={'username': self.lib.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        lib_token = res.data.get('token')

        res = self.client.put(
            path='/api/generic_books/%s/' % gbook.pk,
            data={'title': 'Walking'},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % lib_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        gbook.refresh_from_db()
        self.assertEqual(gbook.title, 'Walking')

    def test_lib_or_sub_read_only_perm_valid_mgr_modif(self):
        gbook = erp_factories.GenericBookFactory.create()
        self.assertNotEqual(gbook.title, 'Walking')

        res = self.client.post(
            path='/api/login/',
            data={'username': self.mgr.user.username,
                  'password': 'fakepwdd'},
            format='json',
        )
        mgr_token = res.data.get('token')

        res = self.client.put(
            path='/api/generic_books/%s/' % gbook.pk,
            data={'title': 'Walking'},
            format='json',
            HTTP_AUTHORIZATION='Token %s' % mgr_token,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        gbook.refresh_from_db()
        self.assertEqual(gbook.title, 'Walking')
