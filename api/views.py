from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.shortcuts import render
from api.serializers import *
from api.models import *
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
from .services.snede_opt_services import *
from .services.user_service import *




# la views de creation de compte utilisateur

class UserApiViews(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            password = make_password(serializer.validated_data['password'])
            # Enregistrement de l'utilisateur avec le mot de passe haché
            serializer.validated_data['password'] = password
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
# La views de connexion des utilisateu

class LoginViews(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '')
        password = request.data.get('password', '')
        registration_method = request.data.get('registration_method', '')

        # Vérifier si l'email est fourni
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier si le mot de passe est fourni
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier si l'utilisateur existe déjà dans la base de données
        user = User.objects.filter(email=email).first()

        # Si l'utilisateur existe déjà et utilise un mot de passe, vérifier le mot de passe
        if user and not registration_method:
            authenticated_user = authenticate(request, email=email, password=password)
            if authenticated_user is not None:
                # Utilisateur authentifié, générer le token
                return super().post(request, *args, **kwargs)
            else:
                # Mot de passe incorrect
                return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)

        # Si l'utilisateur n'existe pas et utilise une méthode de connexion externe
        elif registration_method in ['GOOGLE', 'FACEBOOK', 'APPLE']:
            # Hacher le mot de passe
            hashed_password = make_password(password)
            # Créer un nouvel utilisateur dans la base de données avec le mot de passe haché
            user = User.objects.create(email=email, registration_method=registration_method, password=hashed_password)
            # Générer le token
            return super().post(request, *args, **kwargs)

        else:
            # Email ou méthode d'enregistrement non valide
            return Response({'error': 'Invalid email or registration method'}, status=status.HTTP_400_BAD_REQUEST)
    

