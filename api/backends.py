from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import MultipleObjectsReturned


class PhoneNumberBackend(BaseBackend):

    def authenticate(self, request, phone_number=None, password=None, **kwargs):

        # IMPORTANT
        if not phone_number:
            return None

        UserModel = get_user_model()

        try:
            user = UserModel.objects.get(phone_number=phone_number)

            if user.check_password(password):
                return user

        except UserModel.DoesNotExist:
            return None

        except MultipleObjectsReturned:
            return None

        return None

    def get_user(self, user_id):

        UserModel = get_user_model()

        try:
            return UserModel.objects.get(pk=user_id)

        except UserModel.DoesNotExist:
            return None

        except MultipleObjectsReturned:
            return None