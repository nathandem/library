from datetime import date

from django.db import transaction
from django.shortcuts import get_object_or_404

from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView

from rest_framework import permissions
from rest_framework import status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from library import settings as library_settings # for now, the hard coded way is fine

from erp import models as erp_models
from erp import serializers as erp_serializers
from erp import permissions as erp_permissions


# AUTH

class LoginView(KnoxLoginView):
    """
    The login view must be overwritten, knox doesn't check user's credentials at all!

    POST body is like: {"username": "foo", "password": "bar"}

    For subsequent requests, the token must be provided in a header like this:
    "Authorization: Token xxx" (where xxx is the actual token received from the app)
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response({
            "user": user.username,
            "token": AuthToken.objects.create(user)
        })


# RESOURCE MGT

class LibrarianList(ListCreateAPIView):
    """
    As expected, ListCreateAPIView and its parents provide the same features
    than the standard stuff I manually created below the other resources.

    Note: provide no username, it's auto-generated
    """
    queryset = erp_models.Librarian.objects.all()
    serializer_class = erp_serializers.LibrarianSerializer
    permission_classes = (erp_permissions.IsManager,)


class LibrarianDetail(RetrieveUpdateDestroyAPIView):
    queryset = erp_models.Librarian.objects.all()
    serializer_class = erp_serializers.LibrarianSerializer
    permission_classes = (erp_permissions.IsManager,)


class SubscriberList(PageNumberPagination, APIView):
    """
    Due to a choice of splitting the User information in two tables to maintain
    the default User model clean, the related serializer writes into 2 models.

    The presentation of the empty form is the responsibility of the front app.
    """
    permission_classes = [erp_permissions.IsLibrarian]

    def get(self, request):
        subscribers = erp_models.Subscriber.objects.all()
        page = self.paginate_queryset(subscribers, request, view=self)
        if page is not None:
            serializer = erp_serializers.SubscriberSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = erp_serializers.SubscriberSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriberDetail(APIView):
    permission_classes = [erp_permissions.IsLibrarian]

    def get(self, request, pk):
        subscriber = get_object_or_404(erp_models.Subscriber, pk=pk)
        serializer = erp_serializers.SubscriberSerializer(subscriber)
        return Response(serializer.data)

    def put(self, request, pk):
        subscriber = get_object_or_404(erp_models.Subscriber, pk=pk)
        serializer = erp_serializers.SubscriberSerializer(subscriber, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        subscriber = get_object_or_404(erp_models.Subscriber, pk=pk)
        subscriber.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AuthorList(PageNumberPagination, APIView):
    permission_classes = [erp_permissions.IsLibrarian]

    def get(self, request):
        authors = erp_models.Author.objects.all()
        page = self.paginate_queryset(authors, request, view=self)
        if page is not None:
            serializer = erp_serializers.AuthorSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = erp_serializers.AuthorSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthorDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        author = get_object_or_404(erp_models.Author, pk=pk)
        serializer = erp_serializers.AuthorSerializer(author)
        return Response(serializer.data)

    def put(self, request, pk):
        author = get_object_or_404(erp_models.Author, pk=pk)
        serializer = erp_serializers.AuthorSerializer(author, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        author = get_object_or_404(erp_models.Author, pk=pk)
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenreList(PageNumberPagination, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        genres = erp_models.Genre.objects.all()
        page = self.paginate_queryset(genres, request, view=self)
        if page is not None:
            serializer = erp_serializers.GenreSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = erp_serializers.GenreSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenreDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        genre = get_object_or_404(erp_models.Genre, pk=pk)
        serializer = erp_serializers.GenreSerializer(genre)
        return Response(serializer.data)

    def put(self, request, pk):
        genre = get_object_or_404(erp_models.Genre, pk=pk)
        serializer = erp_serializers.GenreSerializer(genre, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        genre = get_object_or_404(erp_models.Genre, pk=pk)
        genre.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenericBookList(PageNumberPagination, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        generic_books = erp_models.GenericBook.objects.all()
        page = self.paginate_queryset(generic_books, request, view=self)
        if page is not None:
            serializer = erp_serializers.GenericBookSerializerRead(page, many=True)
            return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = erp_serializers.GenericBookSerializerWrite(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GenericBookDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        generic_book = get_object_or_404(erp_models.GenericBook, pk=pk)
        serializer = erp_serializers.GenericBookSerializerRead(generic_book)
        return Response(serializer.data)

    def put(self, request, pk):
        generic_book = get_object_or_404(erp_models.Book, pk=pk)
        serializer = erp_serializers.GenericBookSerializerWrite(generic_book, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        generic_book = get_object_or_404(erp_models.GenericBook, pk=pk)
        generic_book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BookList(PageNumberPagination, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        books = erp_models.Book.objects.all()
        page = self.paginate_queryset(books, request, view=self)
        if page is not None:
            serializer = erp_serializers.BookSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = erp_serializers.BookSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        book = get_object_or_404(erp_models.Book, pk=pk)
        serializer = erp_serializers.BookSerializer(book)
        return Response(serializer.data)

    def put(self, request, pk):
        book = get_object_or_404(erp_models.Book, pk=pk)
        serializer = erp_serializers.BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        book = get_object_or_404(erp_models.Book, pk=pk)
        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# BUSINESS LOGIC

class RentBook(APIView):
    """
    2 steps in the process of giving a rent to a member:
    - 1st: check the subscriber is allowed to rent new books
           This is performed with the GET of this endpoint, only passing the pk of the subscriber.
    - 2nd: if the user can rent, associate the book to the subscriber
           This is performed with the POST of this endpoint, using the data in the body of the request.
    """
    permission_classes = [erp_permissions.IsLibrarian]

    def get(self, request, pk):
        """
        Check whether a subscriber may rent new books.
        Returns: {"can_rent": true, "nb_books_allowed": int, "current_rent_books": [{"title":..., "date_of_return":...}, ...]}
        """
        subscriber = get_object_or_404(erp_models.Subscriber.objects.select_related('user'), pk=pk)
        issues = None
        current_rentals = None

        if subscriber.current_rentals_nb:
            rentals = subscriber.current_rentals
            current_rentals = [{'title': rental.book.generic_book.title, 'date_of_return': rental.due_for} for rental in rentals]

        # subscriber cannot rent
        if not subscriber.can_rent:
            can_rent = False
            nb_books_allowed = 0
            issues = []
            if subscriber.has_rent_issue:
                issues.append({'type': 'has_rent_issue'})
            if not subscriber.valid_subscription:
                issues.append({'type': 'subscription_expired'})
            if subscriber.current_rentals_nb == library_settings.MAX_RENT_BOOKS:
                issues.append({'type': 'max number of books rent reached'})

        # subscriber can rent
        else:
            can_rent = True
            nb_books_allowed = library_settings.MAX_RENT_BOOKS - subscriber.current_rentals_nb

        message = {
            'can_rent': can_rent,
            'nb_books_allowed': nb_books_allowed,
            'current_rentals': current_rentals,
            'issues': issues,
        }
        return Response(message, status=status.HTTP_200_OK if message['can_rent'] else status.HTTP_403_FORBIDDEN)

    def post(self, request, pk): # opti: maybe it'd make more sense to post the books, one by one
        """
        Connect the books to the user, after having check that user can and that they are "Available"

        Request body: {"book_ids": ["id", ...]}
        Response body: {}
        """
        subscriber = get_object_or_404(erp_models.Subscriber.objects.select_related('user'), pk=pk)
        if not subscriber.can_rent:
            return Response(status=status.HTTP_403_FORBIDDEN)

        book_ids = request.data.get('book_ids')
        if not book_ids:
            return Response(data={"detail": "No book_ids were provided"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for book_id in book_ids:
                book = get_object_or_404(erp_models.Book, pk=book_id)
                if not book.status == 'AVAILABLE':
                    return Response(
                        data={"detail": "{} is currently in the status {}".format(book.generic_book.title, book.status)},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                erp_models.Rental.objects.create(user=subscriber.user, book=book)
                book.status = 'RENT'
                book.save()

        # changing type to list is an easy, fast way to serialize objects when used in conjunction
        # with the values() queryset method to get only the good field
        subscriber_rentals = list(subscriber.current_rentals.values('book__generic_book__title', 'due_for'))

        return Response(subscriber_rentals, status=status.HTTP_200_OK)


class ReturnBook(APIView):
    def post(self, request, pk):
        """The opposite of POST on RentBook
        I: book_ids
        O: confirmation that N book.generic_book.title are now returned
            & reminder that N book.generic_book.title are still rent and due for M
        """
        subscriber = get_object_or_404(erp_models.Subscriber, pk=pk)

        book_ids = request.data.get('book_ids')
        if not book_ids:
            return Response({"detail": "No book_ids were provided"}, status=status.HTTP_400_BAD_REQUEST)

        returned_books = []
        today = date.today()
        with transaction.atomic():
            for book_id in book_ids:
                book = erp_models.Book.objects.get(pk=book_id)
                rental = book.current_rental
                if not rental.user == subscriber.user:
                    return Response(
                        data={"detail": "You can't return books that you didn't rent"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                rental.returned_on = today
                if today > rental.due_for:
                    rental.late = True
                    subscriber.received_warning = True
                    subscriber.save()
                rental.save()
                book.status = 'AVAILABLE'
                book.save()
                returned_books.append(book.generic_book.title)

        subscriber_books = list(subscriber.current_rentals.values('book__generic_book__title', 'due_for'))

        msg = {
            'returned_books': returned_books,
            'subscriber_books': subscriber_books
        }

        return Response(msg, status=status.HTTP_200_OK)


class BookGenericBook(APIView):
    """
    Just like with the RentBook view, 2 steps in the process of booking a book:
    - 1st: check the subscriber is allowed to book a new book
           This is performed with the GET of this endpoint, only passing the pk of the subscriber.
    - 2nd: if the user can book, create a booking for him on the generic_book
           This is performed with the POST of this endpoint, using the data in the body of the request.

    Subscribers can reserve/book a book, in two cases:
        - when they are not in the library and wish to reserve a generic book, with an 'AVAILABLE' copy of it
        - when they wish to rent a generic_book, with all its copies are 'RENT' or in 'MAINTENANCE'

    Subscribers book generic_books, not books. A subscriber doesn't want to reserve book_id=679430 which happens to be
    one of the copies of the "The Great Gatsby" the library owns, he wants to book "The Great Gatsby".
    Hence, it's up to us to resolve the translation from generic_book to an actual book.

    #note: later, subscribers will be able to perform their bookings themselves. In this method, we will only have to
    change the way the subscriber_id is received (not through the url but the view context)
    """
    def get(self, request, pk):
        pass

    def post(self, request, pk):
        pass
