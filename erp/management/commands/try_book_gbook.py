from datetime import date
from django.core.management.base import BaseCommand
from erp import models as erp_models


class Command(BaseCommand):
    help = 'Try resolve a booking from a generic_book into a book'

    def handle(self, *args, **kwargs):
        # log the beginning of the job

        subs_with_non_resolved_bookings = erp_models.Subscriber.objects.filter(
            user__bookings__book__isnull=True,
            user__bookings__was_cancelled=False,
        )

        for sub in subs_with_non_resolved_bookings:
            if not sub.can_rent:
                continue
            open_bookings = sub.user.bookings.filter(
                book__isnull=True,
                was_cancelled=False,
            )

            resolved_bookings = []
            for booking in open_bookings:
                # check if the user didn't exceed the booking period
                if booking.is_over:
                    booking.was_cancelled = True
                    sub.didnt_follow_rules()

                book = booking.generic_book.books.filter(status='AVAILABLE').first()
                if book:
                    # mark the booking as resolved
                    booking.book = book
                    booking.book_booked_on = date.today()
                    booking.save()

                    # change the status of the book
                    book.status = 'BOOKED'
                    book.save()

                    resolved_bookings.append(booking)

            # format and send an email to the subscriber for his resolved bookings

        # log the completion of the job


    # def handle(self, *args, **options):
    #     """Starting from the bookings"""
    #     non_resolved_bookings = erp_models.Booking.objects.filter(book__isnull=True)
    #
    #     for booking in non_resolved_bookings:
    #         book = booking.generic_book.books.filter(status='AVAILABLE').first()
    #         if book:
    #             booking.book = book
    #             booking.book_booked_on = date.today()
    #             booking.save()