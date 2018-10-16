from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


# Auth

class Librarian(models.Model):
    """
    Manager librarians can create librarian accounts, rank and file librarians can't.

    Note: librarians' user__username derives from their first and last names
    Note2: librarians don't get attached to the 'Librarians' group automatically,
           no user gets. Need to perform this manually.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_manager = models.BooleanField()

    class Meta:
        ordering = ['user__first_name']

    def __str__(self):
        return self.user.first_name


class Subscriber(models.Model):
    """
    Note: subscribers' user__username == user__email
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address_number_and_street = models.CharField(max_length=70)
    address_zipcode = models.CharField(max_length=20)
    iban = models.CharField(max_length=40)
    subscription_date = models.DateField(default=date.today)
    has_rent_issue = models.BooleanField(default=False)
    received_warning = models.BooleanField(default=False)

    class Meta:
        ordering = ['user__first_name']

    def __str__(self):
        return self.user.first_name

    @property
    def current_rentals(self):
        return self.user.rent_books.exclude(returned_on__isnull=False)

    @property
    def current_bookings(self):
        return self.user.bookings.filter(book=True)

    @property
    def current_rentals_nb(self):
        return self.current_rentals.count() if self.current_rentals else 0

    @property
    def can_rent(self):
        return (
            not self.has_rent_issue
            and self.valid_subscription
            and self.current_rentals_nb < settings.MAX_RENT_BOOKS
        )

    @property
    def valid_subscription(self):
        return date.today() < (self.subscription_date + timedelta(days=settings.SUBSCRIPTION_DAYS_LENGTH))


# Library management

class Author(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class GenericBook(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author, related_name='generic_books', on_delete=models.PROTECT)
    genre = models.ForeignKey(Genre, related_name='generic_books', on_delete=models.PROTECT)
    publication_year = models.IntegerField()

    class Meta:
        ordering = ['title', 'author']

    def __str__(self):
        return self.title


class Book(models.Model):
    BOOK_STATUS = (
        ('AVAILABLE', "Available"),
        ('RENT', "Rent"),
        ('BOOKED', "Booked"),
        ('MAINTENANCE', "Maintenance"),
        ('RETIRED', "Retired")
    )

    CAUSES_BOOK_RETIREMENT = (
        ('WORN', "Worn-out"),
        ('STOLEN', "Stolen"),
        ('NEVER_RETURNED', "Never returned"),
    )

    # Information not changing at each rental (identity of the book)
    generic_book = models.ForeignKey(to=GenericBook, related_name='books', on_delete=models.PROTECT)
    joined_library_on = models.DateField(default=date.today) # make sure the value is not changed each time I update a book
    left_library_on = models.DateField(blank=True, null=True)
    left_library_cause = models.CharField(max_length=15, choices=CAUSES_BOOK_RETIREMENT, blank=True, null=True)

    # Variable information (changing each time the status of the book evolves)
    status = models.CharField(choices=BOOK_STATUS, max_length=20, default='MAINTENANCE')

    class Meta:
        ordering = ['generic_book', 'id']

    def __str__(self):
        return f'{self.generic_book} - {self.pk}'

    def clean(self):
        # even to clean just one field, use this hook
        # clean_fields perform some low-level validation on the type
        self.check_book_properly_left_library()

    def check_book_properly_left_library(self):
        if self.left_library_on and not self.left_library_cause:
            raise ValidationError("A book can't left the library without a cause")
        if self.left_library_cause and not self.left_library_on:
            raise ValidationError("A book can't have a left_cause without a left_library_on date")
        if (self.left_library_on or self.left_library_cause) and not self.status == 'RETIRED':
            raise ValidationError("A book can't left the library and not be retired")
        if self.status == 'RETIRED' and not (self.left_library_on and self.left_library_cause):
            raise ValidationError("A book can't be retired without both left_library_on and left_library_cause filled")

    def save(self, **kwargs):
        self.clean() # to force clean to be used also outside forms and serializers
        super().save(**kwargs)

    @property
    def current_rental(self): # no more than one at the time, otherwise the system is broken somewhere (make a test for this)
        if self.status != 'RENT':
            return None
        return self.rentals.filter(returned_on__isnull=True).first()


class Rental(models.Model):
    """
    This Rental table allows to:
    - keep track of current rentals, allowing to know if a rent is late (send email to subscriber and mark him has_rent_issue)
    - keep track of previous rentals, allowing to perform some analytics on the more, or least, popular GenericBooks
    """
    # fields filled at the creation of the rental
    user = models.ForeignKey(to=User, on_delete=models.PROTECT, related_name='rent_books')
    book = models.ForeignKey(to=Book, on_delete=models.PROTECT, related_name='rentals')
    rent_on = models.DateField(auto_now_add=True)
    due_for = models.DateField() # defined in `self.set_due_for()`

    # fields filled at the end of the rental
    returned_on = models.DateField(blank=True, null=True) # opti: enforce a constraint so that only one record with a given book may have returned_on to NULL
    late = models.BooleanField(default=False)

    def __str__(self):
        return "({}) {} rent by {}".format(
            "Late" if self.late else "Not late",
            self.book.generic_book.title,
            self.user.username
        )

    def save(self, **kwargs):
        is_new = not bool(self.pk)
        if is_new:
            self.set_due_for()
        super().save(**kwargs)

    def set_due_for(self):
        self.due_for = date.today() + timedelta(days=settings.MAX_RENT_DAYS)


class Booking(models.Model):
    """
    Booking holds the record of current and past bookings.

    Subscribers book generic_books, not books. A subscriber doesn't want to reserve book_id=679430 which happens to be
    one of the copies of the "The Great Gatsby" the library owns, he wants to book "The Great Gatsby".
    Hence, it's up to us to resolve the translation from generic_book to an actual book.

    request_made_on is to prioritize who gets his book resolved first, when several subscribers booked the same generic_book.
    book_booked_on stores the date at which the booking of a generic_book has been resolved into a book, starting from
        this date the subscriber has a certain period to withdraw the book (refer to the settings)
    book_withdrawn_during_booking_period tells whether the subscriber played fair with the booking he made,
        or not. If not, the subscriber receives a warning (subscriber.received_warning = True)
    """
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='bookings')
    generic_book = models.ForeignKey(to=GenericBook, on_delete=models.CASCADE, related_name='bookings')
    book = models.ForeignKey(to=Book, on_delete=models.CASCADE, related_name='bookings', blank=True, null=True)
    request_made_on = models.DateField(auto_now_add=True)
    book_booked_on = models.DateField(blank=True, null=True)
    book_withdrawn_during_booking_period = models.BooleanField(blank=True, null=True)

    def __self__(self):
        return "{} booked by {} on {} (resolved: {})".format(self.generic_book, self.user.subscriber,
                                                             self.request_made_on, self.resolved)

    @property
    def resolved(self):
        return bool(self.book)
