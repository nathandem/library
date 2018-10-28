from django.urls import path

from knox import views as knox_views

from erp import views

urlpatterns = [
    ### AUTH
    # Token-based authentication with the knox library
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', knox_views.LogoutView.as_view(), name='logout'),
    path('logoutall/', knox_views.LogoutAllView.as_view(), name='logoutall'),


    ### RESOURCE MGT / RESOURCE-CENTRIC
    # These endpoints mostly act on just one resource (REST principle)
    # They highly rely on DRF's serializers for serialization, deserialization, creation and update
    path('librarians/', views.LibrarianList.as_view()),
    path('librarians/<int:pk>/', views.LibrarianDetail.as_view()),
    path('subscribers/', views.SubscriberList.as_view()),
    path('subscribers/<int:pk>/', views.SubscriberDetail.as_view()),

    path('authors/', views.AuthorList.as_view()),
    path('authors/<int:pk>/', views.AuthorDetail.as_view()),
    path('genres/', views.GenreList.as_view()),
    path('genres/<int:pk>/', views.GenreDetail.as_view()),
    path('generic_books/', views.GenericBookList.as_view()),
    path('generic_books/<int:pk>/', views.GenericBookDetail.as_view()),
    path('books/', views.BookList.as_view()),
    path('books/<int:pk>/', views.BookDetail.as_view()),


    ### BUSINESS LOGIC / PROCESS-CENTRIC
    # These endpoints do more than CRUD operations (span several resources and are process-oriented)
    # They barely not rely on DRF's serializers
    path('rent/<int:sub_pk>/', views.RentBook.as_view()),
    path('return/<int:sub_pk>/', views.ReturnBook.as_view()),
    path('reserve/<int:sub_pk>/', views.ReserveGenericBook.as_view()),
]