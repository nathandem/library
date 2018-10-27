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

        rent_subs = erp_models.Subscriber.objects.filter(user__rent_books=True)
        for rent_sub in rent_subs:
            tight_books = rent_sub.user.rent_books.filter(due_for=four_days_ahead)
            if tight_books: # if tight_books returns an empty Queryset, it evaluates to False
                pass
                # send email using the information of the list



        # self.stdout.write(self.style.SUCCESS('Successfully updated rents'))
        # replace with logging later
