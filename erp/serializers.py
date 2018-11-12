from django.contrib.auth.models import User, Group

from rest_framework import serializers

from . import models as erp_models
from .utils import strip_nonascii


# USER MGT

class RelatedUserValidatorMixin:
    """
    Why using a custom mixin, instead of putting this user validation in UserSerializer?
       self.instance is only available in the model serializer we call directly,
       not the related object. So here, self.instance is only available in
       SubscriberSerializer and LibrarianSerializer, not in UserSerializer.
    Why not using a DRF custom Validator?
       First, their syntax is clumsy > https://www.django-rest-framework.org/api-guide/validators/#writing-custom-validators
       Second, a mixin allow to easy access self.instance

    Note: it's worth noting that DRF first validates related objects, before validating
    the core objects. So when calling LibrarianSerializer or SubscriberSerializer,
    UserSerializer gets validated first, then LibrarianSerializer or SubscriberSerializer.
    Note 2: serializer.validate() is an optional, custom validation hook (like clean() with regular django forms)
    """
    def validate(self, data):
        """
        I want to ensure users provide some optional information (email,
        first_name, last_name) beside the two required ones (username and password).
        """
        # don't the validation for update, they usually don't
        # include all the info and would raise undesired ValidationError
        if self.instance:
            return data

        user_keys = {
            'email': 'The user email is missing',
            'first_name': 'The user first_name is missing',
            'last_name': 'The user last_name is missing',
            'password': 'The user password is missing',
        }

        user = data.get('user')
        for user_key in user_keys:
            if user_key not in user.keys():
                raise serializers.ValidationError(user_keys[user_key])
        return data


class UserSerializer(serializers.ModelSerializer):
    # StringRelatedField are read_only
    # without required=False, DRF raises ValidationError if not here
    # note: because this field is declared here and not in the Meta class,
    #       it's important to pass the field methods here, not
    #       hope it's derived from the Meta class
    groups = serializers.StringRelatedField(many=True, required=False)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'groups', 'is_active')
        read_only_fields = ('username', 'is_active') # ignored if passed in create or update
        write_only_fields = ('password', 'groups') # write_only_fields not hidden when read


class SubscriberSerializer(RelatedUserValidatorMixin, serializers.ModelSerializer):
    """
    See test_serializers for example of working, and non-working, dicts.
    """
    user = UserSerializer() # remind: nested serializers are read-only, but validation occurs on them anyway...

    class Meta:
        model = erp_models.Subscriber
        fields = ('id', 'address_number_and_street', 'address_zipcode', 'subscription_date',
                  'iban', 'has_issue', 'has_received_warning', 'can_rent', 'valid_subscription', 'user')
        read_only_fields = ('id',)

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['username'] = user_data.get('email') # for subscribers, username = email
        user = User.objects.create_user(**user_data)
        subscribers_group = Group.objects.get(name='Subscribers')
        user.groups.add(subscribers_group)
        return erp_models.Subscriber.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if 'user' in validated_data.keys():
            user_data = validated_data.pop('user')
            user_serializer = UserSerializer(instance=instance.user, data=user_data, partial=True)
            if user_serializer.is_valid(raise_exception=True):
                user_serializer.save()
        return super().update(instance, validated_data)


class SubscriberRentalSerializer(serializers.ModelSerializer):
    class Meta:
        model = erp_models.Rental
        fields = ('book', 'rent_on', 'due_for', 'late',) #TODO to be precised


class SubscriberBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = erp_models.Booking
        fields = ('generic_book', 'request_made_on', 'book', 'book_booked_on',) #TODO to be precised


class LibrarianSerializer(RelatedUserValidatorMixin, serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = erp_models.Librarian
        fields = ('id', 'is_manager', 'user')
        read_only_fields = ('id',)

    def generate_username(self, first, last):
        first = strip_nonascii(first).lower().replace(' ', '')
        last = strip_nonascii(last).lower().replace(' ', '')
        n = 1
        while True:
            username = first[0:n] + last
            if not erp_models.User.objects.filter(username=username).exists():
                return username
            if n == 10: # no error raised if we go beyond the end of the string with [a:b]
                raise serializers.ValidationError("Error when trying to generate the username")
            n += 1

    def group_to_join(self, **validated_data):
        if validated_data.get('is_manager'):
            return Group.objects.get(name='Managers')
        return Group.objects.get(name='Librarians')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['username'] = self.generate_username(
            user_data.get('first_name'),
            user_data.get('last_name'),
        )
        user = User.objects.create_user(**user_data)
        group = self.group_to_join(**validated_data)
        user.groups.add(group)
        return erp_models.Librarian.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if 'user' in validated_data.keys():
            user_data = validated_data.pop('user')
            user_ser = UserSerializer(instance=instance.user, data=user_data, partial=True)
            if user_ser.is_valid(raise_exception=True):
                user_ser.save()
        return super().update(instance, validated_data)


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
        # A serializer raises the `required` error only if
        # 1) the field is required by the model (no default or no blank=True),
        # 2) the field received the DRF argument `required=True`
        # here, not passing 'status' at creation is fine as the model
        # provides a default value
        fields = ('id', 'generic_book', 'generic_book_id',
                  'status', 'joined_library_on', 'left_library_on',
                  'left_library_cause')
        depth = 1
