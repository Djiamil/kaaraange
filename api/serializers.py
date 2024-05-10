
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

class ParentChildLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentChildLink
        fields = ['id','slug', 'parent', 'child', 'qr_code']


class ChildSerializerDetail(serializers.ModelSerializer):
    parent_child_link = ParentChildLinkSerializer(read_only=True, source='parentchildlink_set', many=True)
    
    class Meta:
        model = Child
        fields = ['id', 'slug', 'email','password', 'prenom', 'nom', 'is_active', 'is_archive',
                  'user_type', 'accepted_terms', 'registration_method', 'otp_token',
                  'gender', 'date_de_naissance', 'type_appareil', 'numeros_urgences',
                  'ecole', 'allergies', 'parent_child_link']
        
class RetrieveAPIView(serializers.ModelSerializer):
        
        class Meta:
            model = Parent
            fields = '__all__'
