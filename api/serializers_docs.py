from api.models import *
from api.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

#Partie du code pour la documentation de l'api avec drf spectacular
class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    phone_number = serializers.CharField(required=False)
    prenom = serializers.CharField(required=False)
    nom = serializers.CharField(required=False)
    adresse = serializers.CharField(required=False)
    gender = serializers.CharField(required=False)
    avatar = serializers.CharField(required=False)
    registration_method = serializers.CharField(required=False)
    
class UserDocSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    phone_number = serializers.CharField(required=False)
    prenom = serializers.CharField(required=False)
    nom = serializers.CharField(required=False)
class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = UserDocSerializer()
class ErrorSerializer(serializers.Serializer):
    data = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
class PhoneLoginRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()
class PhoneLoginDataSerializer(serializers.Serializer):
    token = serializers.CharField()
    user = UserDocSerializer()


class PhoneLoginResponseSerializer(serializers.Serializer):
    data = PhoneLoginDataSerializer()
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
class SendOtpRequestSerializer(serializers.Serializer):
    telephone = serializers.CharField()
class SendOtpResponseSerializer(serializers.Serializer):
    data = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
class ConfirmOtpRequestSerializer(serializers.Serializer):
    otp_code = serializers.CharField()
class ConfirmOtpResponseSerializer(serializers.Serializer):
    data = serializers.DictField()
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
    
class ChangePasswordRequestSerializer(serializers.Serializer):
    slug = serializers.CharField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()
class ChangePasswordResponseSerializer(serializers.Serializer):
    data = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
class ResendOtpRequestSerializer(serializers.Serializer):
    telephone = serializers.CharField()
class ResendOtpResponseSerializer(serializers.Serializer):
    data = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
    
class SendNotificationRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    title = serializers.CharField(required=False)
class SendNotificationResponseSerializer(serializers.Serializer):
    data = serializers.CharField(allow_null=True, required=False)
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
    
class DeleteUserRequestSerializer(serializers.Serializer):
    phone_or_email = serializers.CharField()
    password = serializers.CharField(required=False)
class DeleteUserResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
class SearchParentRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()
class ParentDocSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.CharField()
    prenom = serializers.CharField()
    nom = serializers.CharField()
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField()
class SearchParentResponseSerializer(serializers.Serializer):
    data = ParentDocSerializer(many=True)
    message = serializers.CharField()
    success = serializers.BooleanField()
    code = serializers.IntegerField()
class ParentRegistrationRequestSerializer(serializers.Serializer):

    prenom = serializers.CharField()

    nom = serializers.CharField()

    email = serializers.EmailField()

    telephone = serializers.CharField()

    password = serializers.CharField()

    adresse = serializers.CharField(required=False)

    gender = serializers.CharField(required=False)

    avatar = serializers.ImageField(required=False)
class ParentRegistrationResponseSerializer(serializers.Serializer):

    data = serializers.DictField()

    message = serializers.CharField()

    success = serializers.BooleanField()

    code = serializers.IntegerField()
class ConfirmParentRegistrationDataSerializer(serializers.Serializer):

    token = serializers.CharField()

    user = UserSerializer()


class ConfirmParentRegistrationResponseSerializer(serializers.Serializer):

    data = ConfirmParentRegistrationDataSerializer()

    message = serializers.CharField()

    success = serializers.BooleanField()

    code = serializers.IntegerField()
class ChildDashboardDocSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    slug = serializers.CharField()

    prenom = serializers.CharField()

    nom = serializers.CharField()
    
class DeviceDashboardDocSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    slug = serializers.CharField()

    nom = serializers.CharField(required=False)

    imei = serializers.CharField(required=False)
class ParentDashboardParentSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    slug = serializers.CharField()

    prenom = serializers.CharField()

    nom = serializers.CharField()

    email = serializers.EmailField()

    phone_number = serializers.CharField()
class ParentDashboardResponseSerializer(serializers.Serializer):

    data = serializers.DictField()

    message = serializers.CharField()

    success = serializers.BooleanField()

    code = serializers.IntegerField()
class EmergencyContactRequestSerializer(serializers.Serializer):

    name = serializers.CharField()

    phone_number = serializers.CharField()

class EmergencyContactDocSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    name = serializers.CharField()

    phone_number = serializers.CharField()
class EmergencyContactResponseSerializer(serializers.Serializer):

    data = serializers.DictField()

    message = serializers.CharField()

    success = serializers.BooleanField()

    code = serializers.IntegerField()

class SendChildAlertRequestSerializer(serializers.Serializer):

    latitude = serializers.FloatField(required=False)

    longitude = serializers.FloatField(required=False)

    adresse = serializers.CharField(required=False)

    location_type = serializers.CharField(required=False)

    wifi_info = serializers.CharField(required=False)

    cell_info = serializers.CharField(required=False)
class SendChildAlertResponseSerializer(serializers.Serializer):

    data = serializers.CharField(allow_null=True, required=False)

    message = serializers.CharField()

    success = serializers.BooleanField()

    code = serializers.IntegerField()
class DeleteChildRequestSerializer(serializers.Serializer):

    slug_parent = serializers.CharField(
        help_text="Slug du parent qui effectue la suppression."
    )
class DeleteChildSuccessSerializer(serializers.Serializer):

    data = serializers.JSONField(
        default=None
    )

    message = serializers.CharField(
        default="Enfant supprimé avec succès"
    )

    success = serializers.BooleanField(
        default=True
    )

    code = serializers.IntegerField(
        default=200
    )


class DeleteChildErrorSerializer(serializers.Serializer):

    data = serializers.JSONField(
        default=None
    )

    message = serializers.CharField()

    success = serializers.BooleanField(
        default=False
    )

    code = serializers.IntegerField()