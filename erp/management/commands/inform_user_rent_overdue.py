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

        late_subs = (
            erp_models.Subscriber.objects
            .exclude(user__rent_books__isnull=True) # can't use model properties in a querysets
            .filter(user__rent_books__returned_on__isnull=True)
            .filter(user__rent_books__due_for__gte=today)
        )

        for late_sub in late_subs:
            # adjust the subscriber status
            if not late_sub.has_rent_issue:
                late_sub.has_rent_issue = True
                late_sub.save()

            # adjust the rental(s) status(es)
            late_books = (
                late_sub.user.rent_books
                .filter(user__rent_books__returned_on__isnull=True)
                .filter(user__rent_books__due_for__gte=today)
            )

            for late_book in late_books:
                if not late_book.late:
                    late_book.late = True
                    late_book.save()

            # prepare and send email to subscriber
            # TODO email formating with jinja?
            # msg = """Dear {}, you passed the rent deadline for {}.
            # You can't rent more until you fix your situation""".format(subscriber, generic_book)
            # TODO backend to send email

        # self.stdout.write(self.style.SUCCESS('Successfully updated rents'))
        # replace with logging later
