

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
        # Exclure le champ 'password' du serializer
        # exclude = ['password']
        fields = '__all__'


class PendingUserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUser
        fields = '__all__'
