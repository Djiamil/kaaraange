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
from django.shortcuts import render, get_object_or_404
from firebase_admin import credentials, messaging 






# la views pour creer le parent temporelement en attendant qu'il valide otp
class parentRegister(generics.CreateAPIView):
    queryset = PendingUser.objects.all()
    serializer_class = PendingUserGetSerializer
    def get(self, request, *args, **kwargs):
        parents = Parent.objects.all()
      
        serializer = UserSerializer(parents, many=True)
        return Response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        serializer = PendingUserGetSerializer(data=request.data)
        user_teste_existence = {}
        user_teste_existence_t = {}
        if serializer.is_valid():
            if request.data.get('email') == "" and request.data.get('telephone') == "":
                return Response({
                    "data" : None,
                    "message" : "Véillez Fournir un email ou un numero de télephone pour l'inscription",
                    "success" : False,
                    "code" : 404
                },status=status.HTTP_400_BAD_REQUEST)
            try:
                user_teste_existence = User.objects.get(email=request.data.get('email'))
            except User.DoesNotExist:
                pass
            if user_teste_existence :
                return Response({
                    "data" : None,
                    "message" : "Un utilisateur avec cette email existe deja",
                    "success" : False,
                    "code" : 404
                },status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user_teste_existence_t = User.objects.filter(phone_number=request.data.get('telephone'))
            except User.DoesNotExist:
                pass
            if user_teste_existence_t :
                return Response({
                    "data" : None,
                    "message" : "Un utilisateur avec ce numero de telephone existe deja",
                    "success" : False,
                    "code" : 404
                },status=status.HTTP_400_BAD_REQUEST)
            if request.data.get('avatar') is None:
                default_avatar_url = "/avatars/Placeholder_Person.jpg"
            pendingUser = serializer.save(avatar=default_avatar_url)
            otp_code = generate_otp(pendingUser)
            to_phone_number = request.data['telephone']
            text = "Veillez recevoir votre code de confirmation d'inscription " + otp_code
            send_sms(to_phone_number, text)
            response_serializer = PendingUserGetSerializer(pendingUser)
            return Response({
                "data" : {
                    "parent" : response_serializer.data
                },
                "message" : "Code de valiidatiion de compte envoyer avec success",
                "success" : True,
                "code" : 201
            },status=status.HTTP_201_CREATED)
        return Response({
                    "data" : None,
                    "message" : serializer.errors,
                    "success" : False,
                    "code" : 400
                }, status=status.HTTP_400_BAD_REQUEST)

# les view previs pour la suppresssion et la modification
class UpdateParent(generics.UpdateAPIView):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    lookup_field = 'slug'

    def put(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        try:
            child = Parent.objects.get(slug=slug)
        except Parent.DoesNotExist:
            return Response({
                "data": None,
                "message": "Ce parent n'existe pas",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        phone_number = request.data.get('phone_number')
        if phone_number is None and not child.phone_number:
            return Response({
                "data": None,
                "message": "Le numéro de téléphone est obligatoire pour modifier le profil",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ParentSerializer(child, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "data": {
                    "child": serializer.data
                },
                "message": "Profil mis à jour avec succès",
                "success": True,
                "code": 200
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "data": None,
                "message": "Les données fournies ne sont pas valides",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)


# confimation de l'inscription du parent apres le saisi de l'otp
class ConfirmRegistration(generics.CreateAPIView):
    def post(self, request):
        otp_code = request.data.get('otp_code')
        if not otp_code:
            return Response({
                "data" : None,
                "message" : 'Le code OTP est requis',
                "success" : False,
                "code" : 400
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            otp = OTP.objects.get(otp_code=otp_code)
        except OTP.DoesNotExist:
            return Response({
                "data" : None,
                "message": 'Code OTP invalide',
                "success" : False,
                "code" : 400
                }, status=status.HTTP_400_BAD_REQUEST)
        pending_user = otp.pending_user
        if pending_user is None:
            return Response({
                "data": None,
                "message": 'Aucun utilisateur en attente de confirmation',
                "success": False,
                "code": 400
                }, status=status.HTTP_400_BAD_REQUEST)
        user = Parent.objects.create(
            phone_number=pending_user.telephone,
            email = pending_user.email,
            prenom=pending_user.prenom,
            nom = pending_user.nom,
            password=make_password(pending_user.password),
            accepted_terms = True,
            adresse = pending_user.adresse,
            gender = pending_user.gender,
            avatar = pending_user.avatar
            )
        pending_user.delete()
        otp.delete()
        return Response({
            "data" : None,
            "message": 'Compte utilisateur créé avec succès',
            "success" : True,
            "code" : 200,
            }, status=status.HTTP_201_CREATED)
    

class CounteUserActifAndUserInactif(generics.GenericAPIView):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer

    def get(self, request, *args, **kwargs):
        parent_actif_count = 0
        parent_inactif_count = 0
        nb_enfant = 0 
        nb_alerts = 0
        parent_actif_liste = []

        parents = Parent.objects.all()
        for parent in parents:
            parent_child_link = FamilyMember.objects.filter(parent=parent).exists()
            if parent_child_link:
                parent_actif_count += 1
                parent_actif_liste.append(parent)
            else:
                parent_inactif_count += 1
        nb_enfant = Child.objects.all().count()
        nb_alerts = EmergencyAlert.objects.filter(state="en_attente").count()
        return Response({
            "data": {
                "nombre_actif": parent_actif_count,
                "nombre_inactif": parent_inactif_count,
                'nb_enfant' :nb_enfant,
                'nb_alerts' : nb_alerts,

            },
            "message": "Le nombre de parents actifs et inactifs",
            "success": True,
            "code": 200
        }, status=status.HTTP_200_OK)
    
class ListeUserActifInactif(generics.GenericAPIView):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer

    def get(self, request, *args, **kwargs):
        parent_actif_liste = []
        parent_inactif_liste = []

        parents = Parent.objects.all()
        for parent in parents:
            parent_child_link = FamilyMember.objects.filter(parent=parent).exists()
            if parent_child_link:
                parent_actif_liste.append(parent)
            else:
                parent_inactif_liste.append(parent)

        parent_actif_liste_serialized = ParentSerializer(parent_actif_liste, many=True).data
        parent_inactif_liste_serialized = ParentSerializer(parent_inactif_liste, many=True).data

        return Response({
            "data": {
                "parent_actif_liste": parent_actif_liste_serialized,
                "parent_inactif_liste": parent_inactif_liste_serialized
            },
            "message": "Le nombre de parents actifs et inactifs",
            "success": True,
            "code": 200
        }, status=status.HTTP_200_OK)

# Cette views nous permetra de lister tous  les information qui concerne le parent
class ParentDashbord(generics.RetrieveAPIView):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    lookup_field = 'slug'

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        try:
            parent = get_object_or_404(Parent, slug=slug)
        except Parent.DoesNotExist:
            return Response({
                "data": None,
                "message": 'Aucun parent trouvé',
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        famille = FamilyMember.objects.filter(parent=parent)
        if not famille.exists():
            return Response({
                "data": None,
                "message": "Ce parent n'est lié à aucun enfant",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        children = [member.child for member in famille]

        return Response({
            "data": {
                "parent": ParentSerializer(parent).data,
                "children": ChildSerializerDetail(children, many=True).data
            },
            'message': 'Détails des enfants',
            'success': True,
            'code': 200
        }, status=status.HTTP_200_OK)
    
# views pour permetre au parent de pouvoir ajouter des numero d'urgence au parent
class ParentAddEmergencyContactForChildAlert(generics.RetrieveAPIView):
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer

    def get(self, request, slug, *args, **kwargs):
        child_contacts = EmergencyContact.objects.filter(parent__slug=slug)
        serializer = EmergencyContactSerializer(child_contacts, many=True)
        return Response({
            "data": {
                "emergency_contact": serializer.data,
            },
            'message': 'Détails des enfants',
            'success': True,
            'code': 200
        }, status=status.HTTP_200_OK)

    def post(self, request, slug, *args, **kwargs):
        parent = Parent.objects.get(slug=slug)
        request.data['parent'] = parent.id  # Ajouter le parent dans les données de la requête
        serializer = EmergencyContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            text = "Bonjour " + request.data.get('name') + ", le parent " + parent.prenom + " " + parent.nom + " vous a ajouté en tant que numéro de contact d'urgence pour ses enfants."
            to_phone_number = request.data['phone_number']
            send_sms(to_phone_number, text)
            return Response ({
                "data": serializer.data,
                'message': "Numero d'urgence ajouté avec succès" ,
                'success': True,
                'code': 200
            },status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# views pour alerter les membre de famille d'un enfant et envoyer la notification via firebase

def send_simple_notification(token,text):
    message = messaging.Message(
        notification=messaging.Notification(
            title='Bonjour,',
            body=text,
        ),
        token=token,
    )
    response = messaging.send(message)
    print('Successfully sent message:', response)

class SendAlertAllEmergenctContactForParentToChild(generics.RetrieveAPIView):
        queryset = EmergencyAlert.objects.all()
        serializer_class = EmergencyAlertSerializer
        def post(self, request, *args, **kwargs):
            slug = kwargs.get('slug')
            latitude = request.data.get('latitude', '')
            longitude = request.data.get('longitude', '')
            adresse = request.data.get('adresse', '')
            try:
                child = Child.objects.filter(slug=slug).first()
                text = f"Vous avez reçu une alerte de votre enfant {child.prenom}."
                alert = EmergencyAlert.objects.create(
                    child=child,
                    alert_type= "Prévenu par l'enfant",
                    comment= text,
                    latitude=latitude,
                    longitude=longitude,
                    adresse=adresse
                )
                family_members = FamilyMember.objects.filter(child=child)
                emergency_contacts = []
                for family_member in family_members:
                    parent = family_member.parent
                    if parent :
                        contacts = EmergencyContact.objects.filter(parent=parent)
                        for contact in contacts:
                            emergency_contacts.append(contact)
                    if parent.fcm_token :
                        token =parent.fcm_token
                        text = f"Vous avez reçu une alerte de votre enfant {child.prenom}."
                        try :
                            send_simple_notification(token,text)
                        except Exception as e:  # Capturer toutes les exceptions
                            print(f"Erreur lors de l'envoi de la notification à {parent}: {e}")
                    AlertNotification.objects.create(alert=alert,type_notification='alerte', parent=parent)
                for contact in emergency_contacts:
                    text = f"Vous avez reçu une alerte de votre enfant {child.prenom}."
                    send_sms(contact.phone_number, text)
                return Response({'data': None, 'message': 'Alert created and emergency contacts notified.',"success": True,"code" : 200}, status=status.HTTP_201_CREATED)
            except Child.DoesNotExist:
                return Response({'data': None, 'message': 'Child not found', 'success':True, "code" : 400}, status=status.HTTP_404_NOT_FOUND)

# Views pour lister les notification d'alerte recu par le parent

class ParentNotificationListe(generics.ListAPIView):
    serializer_class = AlertNotificationSerializer

    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return AlertNotification.objects.filter(parent__slug=slug).order_by('-notified_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({'data': None, 'message': 'Aucune notification pour ce parent', 'success': False, "code" : 400}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data, 'message': 'Notifications du parent.', "success": True, "code": 200}, status=status.HTTP_200_OK)
        
            

