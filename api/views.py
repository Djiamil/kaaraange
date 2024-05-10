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
from api.services.snede_opt_service import *
from .services.user_service import *
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import AccessToken
import io
from django.http import JsonResponse

 

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
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Vérifier si l'utilisateur existe déjà dans la base de données
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        if user:
            if not registration_method:
                authenticated_user = authenticate(request, email=email, password=password)
                if authenticated_user is not None:
                    # Utilisateur authentifié, générer le token d'accès
                    tokens = super().post(request, *args, **kwargs)
                    access_token = AccessToken.for_user(user)
                    serializer = UserSerializer(user)
                    return Response({'token': str(access_token), 'user': serializer.data}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Utilisateur existant, générer le token d'accès et retourner les informations de l'utilisateur
                access_token = AccessToken.for_user(user)
                serializer = UserSerializer(user)  # Utiliser le serializer pour sérialiser l'utilisateur
                return Response({'token': str(access_token), 'user': serializer.data}, status=status.HTTP_200_OK)
        # Si l'utilisateur n'existe pas et utilise une méthode de connexion externe
        elif registration_method in ['GOOGLE', 'FACEBOOK', 'APPLE']:
            # Créer un nouvel utilisateur dans la base de données avec la méthode de connexion externe
            user = User.objects.create(email=email, registration_method=registration_method,password=make_password(password))
            # Générer le token d'accès et retourner les informations de l'utilisateur
            access_token = AccessToken.for_user(user)
            serializer = UserSerializer(user)
            return Response({'token': str(access_token), 'user': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid email or registration method'}, status=status.HTTP_400_BAD_REQUEST)

# Pour tester les envoies sms des code otp
class TestSendSMS(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        message = "Je vous envoie ce SMS pour permettre de valider votre inscription."
        send_sms(request.data)
        return Response({"message": "SMS envoyé avec succès !"}, status=status.HTTP_200_OK)

# views pour lister les relations parent enfant
class lislinkchildtoparent(generics.CreateAPIView):
        serializers = ParentChildLinkSerializer
        queryset = ParentChildLink.objects.all()
        def get (self, request, *args, **kwargs):
            items = ParentChildLink.objects.all()
            serializer = ParentChildLinkSerializer(items, many=True)
            return Response(serializer.data)
        
# views pour afficher le binary du qrcode en image
class GetQRCode(generics.RetrieveAPIView):
    queryset = ParentChildLink.objects.all()
    serializer_class = ParentChildLinkSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        qr_code_base64 = instance.qr_code

        if qr_code_base64:
            try:
                qr_code_base64 = qr_code_base64.replace("b\"", "").replace("\"", "")
                qr_code_bytes = base64.b64decode(qr_code_base64)
                qr_img = qrcode.make(qr_code_bytes)
                pil_image = qr_img.get_image()
                new_width = 400  # largeur souhaitée
                new_height = 400  # hauteur souhaitée
                pil_image_resized = pil_image.resize((new_width, new_height))
                img_io = io.BytesIO()
                pil_image_resized.save(img_io, format='PNG')
                response = HttpResponse(content_type="image/png")
                response.write(img_io.getvalue())

                return response
            except Exception as e:
                return HttpResponse(f"Une erreur s'est produite : {e}", status=500)
        else:
            return HttpResponse("Le QR code n'existe pas pour cet objet.", status=404)

# views pour envoyer le code otp de verification du nemero pour les mot de passe oublier
class SendOtpUserChangePassword(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        to_phone_number = request.data.get('telephone')
        
        if not to_phone_number:
            return JsonResponse({'error': 'Numéro de téléphone manquant'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            parent = Parent.objects.get(telephone=to_phone_number)
        except Parent.DoesNotExist:
            return JsonResponse({'error': 'Parent non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        otp_code = generate_otp()
        text = f"Votre code de vérification pour changer le mot de passe est : {otp_code}"
        send_sms(to_phone_number, text)

        parent.otp_token = otp_code
        parent.save()

        return JsonResponse({'message': 'OTP envoyé avec succès'}, status=status.HTTP_200_OK)

# views pour la confirmation de l'otp pour la modificatiion du password
class ConfirmOtpUserForPassword(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        otp_code = request.data.get('otp_code')
        
        if not otp_code:
            return JsonResponse({'error': 'Code OTP manquant'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(otp_token=otp_code)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Code de confirmation incorecte'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)

# views pour la modification du password de l'utlisateur
class ChangePasswordUser(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        slug = request.data.get('slug')
        password1 = request.data.get('password1')
        password2 = request.data.get('password2')

        if not password1 or not password2:
            return JsonResponse({'error': 'Veillez renseignez le password1 et le password2'}, status=status.HTTP_400_BAD_REQUEST)

        if password1 != password2:
            return JsonResponse({'error': 'Les mots de passe ne correspondent pas'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(slug=slug)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

        user.password = make_password(password1)
        user.save()

        return JsonResponse({'message': 'Votre mot de passe a été modifié avec succès'}, status=status.HTTP_200_OK)




        







