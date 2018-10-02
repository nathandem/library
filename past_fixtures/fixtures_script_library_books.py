import os
import json

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')
django.setup()

from erp.models import Author, Genre, GenericBook


# fixtures
fiction = Genre.objects.get(name='Fiction')

with open('../100_books.json', 'r') as text_file:
    books = json.load(text_file)

for book in books:
    title = book['title']
    book_author = book['author']
    author = Author.objects.get_or_create(name=book_author)
    # try:
    # 	author = Author.objects.get(name=book_author)
    # except:
    # 	author = Author.objects.create(name=book_author)
    genre = fiction
    publication_year = book['year']

    GenericBook.objects.create(
        title=title,
        author=author,
        genre=genre,
        publication_year=publication_year
    )


#####
# Factory boy allows for a close result but not entirely
# issue: BookFactory creates a new author even when this author already exists

# import factory
#
#
# class AuthorFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = Author
#     name = factory.Iterator(books, cycle=False, getter=lambda c: c['author'])
#
#
# class BookFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = Book
#     title = factory.Iterator(books, cycle=False, getter=lambda c: c['title'])
#     author = factory.SubFactory(AuthorFactory)
#     genre = Genre.objects.get(name='Fiction')
#     title = factory.Iterator(books, cycle=False, getter=lambda c: c['year'])
