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
from rest_framework.views import APIView


 

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
    
# La views de connexion des utilisateur
class LoginViews(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '')
        phone_number = request.data.get('phone_number')
        prenom = request.data.get('prenom', '')
        nom = request.data.get('nom', '')
        adresse = request.data.get('adresse', '')
        gender = request.data.get('gender', '')
        avatar = request.data.get('avatar', '')
        password = request.data.get('password', '')
        registration_method = request.data.get('registration_method', '')
        if not email:
            return Response({'data': None,'message': 'Email is required', 'success': False, 'code' : 400}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'data': None, 'message': 'Password is required', 'sucess' : False , 'code' : 400}, status=status.HTTP_400_BAD_REQUEST)
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
                    return Response({ 'data' : {'token': str(access_token),'user': serializer.data}, 'success' : True, 'code' : 200 }, status=status.HTTP_200_OK)
                else:
                    return Response({'data': None,'message': 'Invalid password', 'success': False, 'code' : 400}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Utilisateur existant, générer le token d'accès et retourner les informations de l'utilisateur
                access_token = AccessToken.for_user(user)
                serializer = UserSerializer(user)  # Utiliser le serializer pour sérialiser l'utilisateur
                return Response({ 'data' : {'token': str(access_token),'user': serializer.data}, 'success' : True, 'code' : 200 }, status=status.HTTP_200_OK)
        # Si l'utilisateur n'existe pas et utilise une méthode de connexion externe
        elif registration_method in ['GOOGLE', 'FACEBOOK', 'APPLE']:
            # Créer un nouvel utilisateur dans la base de données avec la méthode de connexion externe
            user = Parent.objects.create(email=email,
                                         phone_number=phone_number,
                                         prenom = prenom,
                                         nom = nom,
                                         adresse=adresse,
                                         gender = gender,
                                         avatar = avatar,
                                         registration_method=registration_method,password=make_password(password))
            # Générer le token d'accès et retourner les informations de l'utilisateur
            access_token = AccessToken.for_user(user)
            serializer = UserSerializer(user)
            return Response({ 'data' : {'token': str(access_token),'user': serializer.data}, 'success' : True, 'code' : 200 }, status=status.HTTP_200_OK)
        else:
            return Response({'data': None, 'message': 'Invalid email or registration method', 'success': False, 'code': 400}, status=status.HTTP_400_BAD_REQUEST)

# connexiion pr numero de telephone
class PhoneLoginView(APIView):
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number', '')
        password = request.data.get('password', '')

        if not phone_number:
            return Response({
                'data': None,
                'message': 'Phone number is required',
                'success': False,
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({
                'data': None,
                'message': 'Password is required',
                'success': False,
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authentifier l'utilisateur avec le backend personnalisé
        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None:
            access_token = AccessToken.for_user(user)
            serializer = UserSerializer(user)
            return Response({
                'data': {
                    'token': str(access_token),
                    'user': serializer.data,
                },
                'message': 'Login successful',
                'success': True,
                'code': 200,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'data': None,
                'message': 'Invalid phone number or password',
                'success': False,
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)

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
            return JsonResponse({
                        'data' : None,
                        'message': 'Numéro de téléphone manquant',
                        'success' : False,
                        'code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
        try:
            parent = User.objects.get(phone_number=to_phone_number)
        except User.DoesNotExist:
            return JsonResponse({
                'data' : None,
                'message': 'Utilisateur non trouvé',
                'succeed' : False,
                'code': 404
                }, status=status.HTTP_404_NOT_FOUND)

        otp_code = generate_otp()
        text = f"Pour garantir la sécurité de votre compte, veuillez utiliser ce code pour changer votre mot de passe : {otp_code}. Ensemble, nous veillons sur ce qui compte le plus."
        send_sms(to_phone_number, text)

        parent.otp_token = otp_code
        parent.save()

        return JsonResponse({
                        'data' :None,
                        'message': 'OTP envoyé avec succès',
                        'success' : True,
                        'code': 200
                }, status=status.HTTP_200_OK)

# views pour la confirmation de l'otp pour la modificatiion du password
class ConfirmOtpUserForPassword(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        otp_code = request.data.get('otp_code')
        
        if not otp_code:
            return JsonResponse({
                        'data': None,
                        'message': 'Code OTP manquant',
                        'success': False,
                        'code': 400
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(otp_token=otp_code)
        except User.DoesNotExist:
            return JsonResponse({
                "data" : None,
                'message': 'Code de confirmation incorecte',
                'success' : False,
                'code' : 400
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(user)
        return Response({
                'data': {
                    "user": serializer.data
                },
                "message": "Verification de cote de confirmatiiiion avec success",
                "success" : True,
                "code": 200
                },status=status.HTTP_201_CREATED)

# views pour la modification du password de l'utlisateur
class ChangePasswordUser(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        slug = request.data.get('slug')
        password1 = request.data.get('password1')
        password2 = request.data.get('password2')

        if not password1 or not password2:
            return JsonResponse({
                    'data' : None,
                    'message': 'Veillez renseignez le password1 et le password2',
                    'success' : False,
                    'code' : 400
                }, status=status.HTTP_400_BAD_REQUEST)

        if password1 != password2:
            return JsonResponse({
                'data' : None,
                'message': 'Les mots de passe ne correspondent pas',
                'success' : False,
                'code' : 400
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(slug=slug)
        except User.DoesNotExist:
            return JsonResponse({
                    'data': None,
                    'message': 'Utilisateur non trouvé',
                    'success': False,
                    'code': 404,
                }, status=status.HTTP_404_NOT_FOUND)

        user.password = make_password(password1)
        user.save()

        return JsonResponse({
                    'data': None,
                    'message': 'Votre mot de passe a été modifié avec succès',
                    'success': True,
                    "code": 200
                }, status=status.HTTP_200_OK)


class listeAlert(generics.GenericAPIView):
        alerts = EmergencyAlert.objects.all()
        serializer_class = EmergencyAlertSerializer
        def get(self, request):
            alerts = EmergencyAlert.objects.all()
            serializers = EmergencyAlertSerializer(alerts,many=True)
            return Response(serializers.data)


# Permet de renvoyer le code otp si l'utilisateur s'inscrie dabord et qu'il n'a pas reçu de code otp
class sendBackOtp(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        to_phone_number = request.data.get('telephone')
        if not to_phone_number:
            return JsonResponse({
                'data': None,
                'message': 'Numéro de téléphone manquant',
                'success': False,
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            parent = PendingUser.objects.filter(telephone=to_phone_number).last()
        except PendingUser.DoesNotExist:
            return JsonResponse({
                'data': None,
                'message': 'Utilisateur non trouvé',
                'success': False,
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)

        otp_code = regenerate_otp()

        text = f"Bienvenue dans notre communauté ! Voici votre code de confirmation pour activer votre compte et commencer à veiller sur vos enfants :  {otp_code}."
        send_sms(to_phone_number, text)

        try:
            otp = OTP.objects.filter(pending_user=parent).last()
            otp.otp_code = otp_code
            otp.save()
        except OTP.DoesNotExist:
            return JsonResponse({
                'data': None,
                'message': 'Aucun OTP trouvé pour cet utilisateur',
                'success': False,
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)

        return JsonResponse({
            'data': None,
            'message': 'OTP envoyé avec succès',
            'success': True,
            'code': 200
        }, status=status.HTTP_200_OK)


# Cette views vas juste nous permetre d'envoyer des notification au utilisateur via firedabase
class sendNotificationOnly(generics.GenericAPIView):
    serializer_class = AlertNotificationSerializer
    queryset = AlertNotification.objects.all()
    def post(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        text = request.data.get('text')
        title = request.data.get('title', "Bonjour") 
        if not text:
            return Response({"data": None, "message": "Le texte ne doit pas être vide", "succes" : False , "code" : 400}, status=status.HTTP_400_BAD_REQUEST)
        try :
            user = User.objects.get(slug=slug)
        except User.DoesNotExist:
            return Response({"data" : None , "message" : "Aucun utilisateur trouver pour se mail" , "success" : False, "code" : 404}, status.HTTP_404_NOT_FOUND)
        token = user.fcm_token
        to_phone_number = user.phone_number
        if token :
            message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=text,
            ),
            token=token,
            )
            response = messaging.send(message)
            print('Successfully sent message:', response)
            send_sms(to_phone_number, text)
            return Response({"data" : None, "message" : "Notification envoyer avec succés", "success" : True, "code" : 200}, status = status.HTTP_200_OK)
        elif to_phone_number:
            send_sms(to_phone_number, text)
            return Response({"data" : None, "message" : "Notification envoyer avec succés", "success" : True, "code" : 200}, status = status.HTTP_200_OK)
        else:
            return Response({"data": None, "message": "Aucun moyen de contact trouvé pour cet utilisateur", "success": False, "code": 400},
                            status=status.HTTP_400_BAD_REQUEST)

