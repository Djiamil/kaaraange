
from api.models import *
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer




class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user_id'] = user.id
        data['email'] = user.email
        data['user_type'] = user.user_type
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # exclude = ['password']
        fields = '__all__'

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        # exclude = ['password']
        fields = '__all__'

class PendingUserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUser
        fields = '__all__'

class OtpGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = '__all__'

class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = '__all__'
        lookup_field = 'slug'

class ParentChildLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentChildLink
        fields = ['id','slug', 'child', 'qr_code']

class ChildAlergySerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergy
        fields = ['id', 'child', 'allergy_type', 'description', 'date_identified']
        
class ChildSerializerDetail(serializers.ModelSerializer):
    allergies = ChildAlergySerializer(read_only=True, many=True)

    
    class Meta:
        model = Child
        fields = ['id', 'slug', 'email','phone_number','password', 'prenom', 'nom', 'is_active', 'is_archive',
                  'user_type', 'accepted_terms', 'registration_method', 'otp_token',
                  'gender', 'date_de_naissance', 'type_appareil', 'numeros_urgences',
                  'ecole', 'allergies']
        
class RetrieveAPIView(serializers.ModelSerializer):
        
        class Meta:
            model = Parent
            fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = '__all__'

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'parent', 'name', 'phone_number', 'relationship']

class EmergencyAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model =EmergencyAlert
        fields = '__all__'