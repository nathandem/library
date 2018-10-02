from datetime import date, timedelta
from django.core.management.base import BaseCommand
from erp import models as erp_models


class Command(BaseCommand):
    help = 'Inform concerned users that their rent is overdue'

    def handle(self, *args, **options):
        """
        look for rentals that are overdue (due_for > today):
            - email to inform
            - subscriber.has_rent_issue = True
            - rental.late = True
        """
        today = date.today()

        overdue_rents = erp_models.Rental.objects.filter(due_for__gte=today)

        for overdue_rent in overdue_rents:
            # adjust subscriber information
            subscriber = overdue_rent.user.subscriber
            subscriber.has_rent_issue = True
            subscriber.save()

            # adjust rental information
            overdue_rent.late = True
            overdue_rent.save()

            # send email to subscriber
            generic_book = overdue_rent.book.generic_book.title # the subscriber doesn't reason in terms on books
            msg = """Dear {}, you passed the rent deadline for {}.
            You can't rent more until you fix your situation""".format(subscriber, generic_book)
            # send email with backend

        # self.stdout.write(self.style.SUCCESS('Successfully updated rents'))
        # replace with logging later
