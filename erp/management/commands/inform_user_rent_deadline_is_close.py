from datetime import date, timedelta
from django.core.management.base import BaseCommand
from erp import models as erp_models


class Command(BaseCommand):
    help = 'Inform concerned users that their renting deadline is close'

    def handle(self, *args, **options):
        """
        look for rentals that are 4 close to due_for
            - send email
        """
        today = date.today()
        four_days_ahead = today + timedelta(days=4)

        tight_rents = erp_models.Rental.objects.filter(due_for=four_days_ahead)

        for tight_rent in tight_rents:
            subscriber = tight_rent.user.subscriber
            generic_book = tight_rent.book.generic_book.title # the subscriber doesn't reason in terms on books
            msg = "Dear {}, the rent deadline for {} is in 4 days".format(subscriber, generic_book)
            # send email with backend

        # Opti: start with a subscriber to make sure a given subscriber just gets 1 email, even if he has several books close to the deadline

        # non optimized way
        # get subscribers
        # for each sub,
        #       - loop on his books
        #              - add the ones due_for=four_days_ahead
        #    send an email

        # more optimized way (done below)
        # get subscriber with user.rent_books existing
        # do the same than above (for each sub......)

        # better way?
        # 1 queryset to get subscriber with 1 or more books due_for in four days
        # for each sub, 1 queryset to get the books due in 4 days

        # paradise
        # 1 queryset to get this dict/json
        """
        [
          {
            "tight_subscriber": "John",
            "books": ["Zorba the Greek", "Lord of the Ring"]
          },
          {
            ...
          },
          ...
        ]   
        """
        rent_subs = erp_models.Subscriber.objects.filter(user__rent_books=True)
        for rent_sub in rent_subs:
            tight_books = rent_sub.user.rent_books.filter(due_for=four_days_ahead)
            if tight_books: # if tight_books returns an empty Queryset, it evaluates to False
                pass
                # send email using the information of the list




        # self.stdout.write(self.style.SUCCESS('Successfully updated rents'))
        # replace with logging later
