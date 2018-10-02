from django.contrib.auth.models import User

from rest_framework import serializers

from . import models as erp_models


# USER MGT

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'is_active')
        read_only_fields = ('username',)
        write_only_fields = ('password',)


class SubscriberSerializer(serializers.ModelSerializer):
    """
    Warning: be sure to always pass nested objects' fields, one level
    below the fields of the object of the ModelSerializer.
    Example response for a GET:
    {
      "address_number_and_street": "1, rue de la Paix",
      "address_zipcode": "75001",
      "has_rent_issue": false,
      "iban": "1234",
      "subscription_date": "2018-09-18",
      "user": {
        "username": "jack.cash@g.co",
        "password": "fakepwdd",
        "email": "jack.cash@g.co",
        "first_name": "Jack",
        "last_name": "Cash",
        "id": 7,
      }
    }
    """
    user = UserSerializer()

    class Meta: #TODO include current rentals and bookings
        model = erp_models.Subscriber
        fields = ('id', 'address_number_and_street', 'address_zipcode', 'subscription_date',
                  'iban', 'has_rent_issue', 'can_rent', 'subscription_expired', 'user')
        read_only_fields = ('id',)

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['username'] = user_data.get('email') # for subscribers, username = email
        user = User.objects.create_user(**user_data)
        return erp_models.Subscriber.objects.create(user=user, **validated_data)


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = erp_models.Author
        fields = ('id', 'name',)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = erp_models.Genre
        fields = ('id', 'name',)


# author and genre are string
class GenericBookSerializerRead(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    genre = serializers.StringRelatedField()

    class Meta:
        model = erp_models.GenericBook
        fields = ('id', 'title', 'author', 'genre', 'publication_year',)


# author and genre are integer/id (default behavior for related fields)
class GenericBookSerializerWrite(serializers.ModelSerializer):
    class Meta:
        model = erp_models.GenericBook
        fields = ('id', 'title', 'author', 'genre', 'publication_year',)


class BookSerializer(serializers.ModelSerializer):
    generic_book = GenericBookSerializerRead(read_only=True)
    generic_book_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        source='generic_book',
        queryset=erp_models.GenericBook.objects.all()
    )

    class Meta:
        model = erp_models.Book
        fields = ('id', 'generic_book', 'generic_book_id', 'status')
        depth = 1
