from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.shortcuts import render
from api.serializers import *
from api.models import *
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate
from api.services.snede_opt_service import *
from .services.user_service import *
from rest_framework import status
from rest_framework.pagination import PageNumberPagination



# la views de l'inscription du parent
class parentRegister(generics.CreateAPIView):
    queryset = PendingUser.objects.all()
    serializer_class = PendingUserGetSerializer

    def get(self, request, *args, **kwargs):
        parents = Parent.objects.all()
      
        serializer = UserSerializer(parents, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = PendingUserGetSerializer(data=request.data)
        if serializer.is_valid():
            pendingUser = serializer.save()
            otp_code = generate_otp(pendingUser)
            to_phone_number = request.data['telephone']
            text = "Veillez recevoir votre code de confirmation d'inscription " + otp_code
            send_sms(to_phone_number, text)
            # Retourner les détails du pendingUser créé
            response_serializer = PendingUserGetSerializer(pendingUser)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request):
        parent = Parent.objects.all()
        return Response("je suis dans la methode delete")
    def update(self, request):
        parent = Parent.objects.all()
        return Response("Je suis dans la methode update")

# confimation de l'inscription du parent apres le saisi de l'otp
class ConfirmRegistration(generics.CreateAPIView):
    def post(self, request):
        # Récupérer le code OTP de la requête
        otp_code = request.data.get('otp_code')

        # Vérifier si le code OTP est fourni
        if not otp_code:
            return Response({'error': 'Le code OTP est requis'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier si le code OTP est valide
        try:
            otp = OTP.objects.get(otp_code=otp_code)
        except OTP.DoesNotExist:
            return Response({'error': 'Code OTP invalide'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifier si le code OTP correspond au PendingUser
        pending_user = otp.pending_user
        if pending_user is None:
            return Response({'error': 'Aucun utilisateur en attente de confirmation'}, status=status.HTTP_400_BAD_REQUEST)

        # Créer le compte utilisateur définitif
        user = User.objects.create_user(username=pending_user.telephone, first_name=pending_user.prenom, password=make_password(pending_user.mot_de_passe))

        # Supprimer le PendingUser et l'OTP
        pending_user.delete()
        otp.delete()

        # Retourner une réponse de succès
        return Response({'success': 'Compte utilisateur créé avec succès'}, status=status.HTTP_201_CREATED)