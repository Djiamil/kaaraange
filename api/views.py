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
from safedelete.models import HARD_DELETE
from firebase_admin import credentials, messaging 
from drf_spectacular.utils import extend_schema
from .serializers_docs import *





 

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
@extend_schema(
    tags=["Authentication"],
    summary="Connexion utilisateur",
    description="""
Connexion utilisateur avec plusieurs modes :

- Email + password classique
- Login social (Google / Facebook / Apple)
- Auto-création utilisateur si nécessaire

Retourne un JWT token + informations utilisateur.
""",
    request=LoginRequestSerializer,
    responses={
        200: LoginResponseSerializer,
        400: ErrorSerializer,
        401: ErrorSerializer,
    }
)
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
            user = User.objects.filter(email=email).first()
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
@extend_schema(
    tags=["Authentication"],
    summary="Connexion par numéro de téléphone",
    description="""
Connexion utilisateur via numéro de téléphone et mot de passe.

Retourne un JWT token + informations utilisateur.
""",
    request=PhoneLoginRequestSerializer,
    responses={
        200: PhoneLoginResponseSerializer,
        400: ErrorSerializer,
    }
)
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

@extend_schema(
    tags=["Authentication"],
    summary="Envoi OTP pour changement de mot de passe",
    description="""
Envoie un code OTP par SMS au numéro de téléphone de l'utilisateur.

Ce code est utilisé pour réinitialiser le mot de passe.
""",
    request=SendOtpRequestSerializer,
    responses={
        200: SendOtpResponseSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    }
)
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
@extend_schema(
    tags=["Authentication"],
    summary="Vérification du code OTP",
    description="""
Vérifie le code OTP envoyé par SMS.

Si le code est valide :
- retourne les informations utilisateur
- permet de passer à l'étape changement de mot de passe
""",
    request=ConfirmOtpRequestSerializer,
    responses={
        200: ConfirmOtpResponseSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    }
)
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
@extend_schema(
    tags=["Authentication"],
    summary="Changement de mot de passe",
    description="""
Permet à un utilisateur de changer son mot de passe après validation OTP.

Étapes :
1. Vérification slug utilisateur
2. Vérification password1 == password2
3. Hash et mise à jour du mot de passe
""",
    request=ChangePasswordRequestSerializer,
    responses={
        200: ChangePasswordResponseSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    }
)
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
@extend_schema(
    tags=["Authentication"],
    summary="Renvoyer OTP d'activation de compte",
    description="""
Permet de renvoyer un nouveau code OTP à un utilisateur en attente d'activation.

Étapes :
1. Vérifie le numéro de téléphone
2. Récupère le PendingUser
3. Génère un nouveau OTP
4. Met à jour le dernier OTP existant
5. Envoie le SMS
""",
    request=ResendOtpRequestSerializer,
    responses={
        200: ResendOtpResponseSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    }
)
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
@extend_schema(
    tags=["Notification"],
    summary="Envoyer une notification push à un utilisateur",
    description="""
Envoie une notification push via Firebase Cloud Messaging (FCM).

- Si l'utilisateur a un token FCM → notification push
- Sinon fallback possible SMS (désactivé actuellement)

Types supportés :
- Chat notification
""",
    request=SendNotificationRequestSerializer,
    responses={
        200: SendNotificationResponseSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    }
)
class sendNotificationOnly(generics.GenericAPIView):
    serializer_class = AlertNotificationSerializer
    queryset = AlertNotification.objects.all()
    def post(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        text = request.data.get('text')
        title = request.data.get('title', "Bonjour") 
        # chat_sound
        if not text:
            return Response({"data": None, "message": "Le texte ne doit pas être vide", "succes" : False , "code" : 400}, status=status.HTTP_400_BAD_REQUEST)
        try :
            user = User.objects.get(slug=slug)
        except User.DoesNotExist:
            return Response({"data" : None , "message" : "Aucun utilisateur trouver pour se mail" , "success" : False, "code" : 404}, status.HTTP_404_NOT_FOUND)
        token = user.fcm_token
        to_phone_number = user.phone_number
        if token:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=text,
                ),
                data={
                    "type": "chat"
                },
                token=token,

                # Configuration iOS
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="chat_sound.aiff"
                        )
                    )
                ),

                # Configuration Android
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="chat_sound",
                        channel_id="chat_channel"
                    )
                )
            )

            response = messaging.send(message)
            print('Successfully sent message:', response)
            # send_sms(to_phone_number, text)
            return Response({"data" : None, "message" : "Notification envoyer avec succés", "success" : True, "code" : 200}, status = status.HTTP_200_OK)
        # elif to_phone_number:
        #     send_sms(to_phone_number, text)
        #     return Response({"data" : None, "message" : "Notification envoyer avec succés", "success" : True, "code" : 200}, status = status.HTTP_200_OK)
        else:
            return Response({"data": None, "message": "Aucun moyen de contact trouvé pour cet utilisateur", "success": False, "code": 400},
                            status=status.HTTP_400_BAD_REQUEST)
@extend_schema(
    tags=["Authentication"],
    summary="Supprimer un utilisateur",
    description="""
Supprime définitivement un utilisateur à partir de son email ou de son numéro de téléphone.

Comportement :

- recherche l'utilisateur
- si l'utilisateur est un parent :
    - supprime les enfants associés
    - supprime les relations FamilyMember
- supprime ensuite le compte utilisateur

⚠️ Cette suppression est définitive.
""",
    request=DeleteUserRequestSerializer,
    responses={
        200: DeleteUserResponseSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    }
)
class DeleteUserView(generics.DestroyAPIView):
    def delete(self, request, *args, **kwargs):
        phone_or_email = request.data.get("phone_or_email")
        password = request.data.get('password')  # Si jamais tu veux vérifier un jour

        if not phone_or_email:
            return Response(
                {"message": "Veuillez fournir un email ou un numéro de téléphone", "success": False, "code": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Trouver l'utilisateur par email ou téléphone
        user = User.objects.filter(email=phone_or_email).first() or User.objects.filter(phone_number=phone_or_email).first()

        if not user:
            return Response(
                {"message": "Utilisateur non trouvé", "success": False, "code": 404},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.user_type == "PARENT":
            family_members = FamilyMember.objects.filter(parent=user)
            for family_member in family_members:
                family_member.child.delete()
            family_members.delete()

        user.delete(force_policy=HARD_DELETE)

        return Response(
            {"message": "Utilisateur supprimé avec succès", "success": True, "code": 200},
            status=status.HTTP_200_OK,
        )

@extend_schema(
    tags=["Authentication"],
    summary="Rechercher un utilisateur par téléphone",
    description="""
Recherche un ou plusieurs utilisateurs à partir d'un numéro de téléphone.

Retourne les informations des utilisateurs correspondants.
""",
    request=SearchParentRequestSerializer,
    responses={
        200: SearchParentResponseSerializer,
        400: ErrorSerializer,
        404: ErrorSerializer,
    }
)
class SearchUserForPhone(APIView):

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get("phone")
        if not phone_number:
            return Response({"message": "Le champ 'phone' est requis", "success": False, "code": 400},
                            status=status.HTTP_400_BAD_REQUEST)

        parents = Parent.objects.filter(phone_number=phone_number)
        if not parents.exists():
            return Response({"message": "Aucun utilisateur avec ce téléphone", "success": False, "code": 404},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = ParentSerializer(parents, many=True)
        return Response({"data": serializer.data, "message": "Utilisateur(s) récupéré(s) avec succès",
                         "code": 200, "success": True}, status=status.HTTP_200_OK)
