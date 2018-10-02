"""
Create books with available books in the DB

Book attributes are: id, book, due_back, status (4 choices)
"""
# set-up django
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')
django.setup()


# create books
import datetime

from erp.models import GenericBook, Book

books = Book.objects.all()[3:]

for book in books:
    for n in range(5):
        if n == 0 or n == 1:
            status = 'RENTED'
            due_back = datetime.date.today() + datetime.timedelta(days=30)
        elif n == 2:
            status = 'BOOKED'
        elif n == 3:
            status = 'AVAILABLE'
        else:
            status = 'MAINTENANCE'
        GenericBook.objects.create(
            status=status,
            due_back=due_back,
            book=book
        )
        due_back = None
