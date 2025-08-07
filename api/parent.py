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
import math
from django.utils import timezone
from datetime import timedelta






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
                if request.data.get('email') == None:
                    return Response({"data" : None, "message" : "Véillez Fournir un email", "success" : False, "code" : 404},status=status.HTTP_400_BAD_REQUEST)
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
            text = "Bienvenue dans notre communauté ! Voici votre code de confirmation pour activer votre compte et commencer à veiller sur vos enfants : " + otp_code + "."
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
from itertools import chain

class ParentDashbord(generics.RetrieveAPIView):
    queryset = Parent.objects.all()
    serializer_class = ParentSerializer
    lookup_field = 'slug'

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        parent = get_object_or_404(Parent, slug=slug)

        famille = FamilyMember.objects.filter(parent=parent)
        if not famille.exists():
            return Response({
                "data": None,
                "message": "Ce parent n'est lié à aucun enfant",
                "success": True,
                "code": 200
            }, status=status.HTTP_200_OK)

        # Filtrer les enfants non null
        children = [member.child for member in famille if member.child]
        devices = [member.device for member in famille if member.device]

        serialized_children = ChildSerializerDetail(children, many=True).data
        serialized_devices = DeviceSerializerDetail(devices, many=True).data

        # Tu peux soit les fusionner dans une seule liste, soit les séparer dans deux clés
        all_linked = serialized_children + serialized_devices

        return Response({
            "data": {
                "parent": ParentSerializer(parent).data,
                "children": all_linked,
            },
            'message': 'Détails des enfants et appareils liés',
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
            text = "Bonjour " + request.data.get('name') + ", le parent " + parent.prenom + " " + parent.nom + " vous fait confiance et vous a désigné(e) comme contact d'urgence pour ses enfants. Merci pour votre soutien précieux."
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
class SendAlertAllEmergenctContactForParentToChild(generics.RetrieveAPIView):
        queryset = EmergencyAlert.objects.all()
        serializer_class = EmergencyAlertSerializer
        def post(self, request, *args, **kwargs):
            slug = kwargs.get('slug')
            latitude = request.data.get('latitude', '')
            longitude = request.data.get('longitude', '')
            adresse = request.data.get('adresse', '')
            wifi_info = request.data.get('wifi_info', '')
            cell_info = request.data.get('cell_info', '')
            device = Device.objects.filter(imei=slug).first()
            if device :
                location_type = request.data.get('location_type', '')
                text = f"Vous avez reçu une alerte de votre enfant {device.nom}."
                alert = EmergencyAlert.objects.create(
                    device=device,
                    alert_type= "Prévenu par l'enfant",
                    comment= text,
                    latitude=latitude,
                    longitude=longitude,
                    location_type = location_type,
                    wifi_info = wifi_info,
                    cell_info = cell_info
                )
                family_members = FamilyMember.objects.filter(device=device)
                emergency_contacts = []
                for family_member in family_members:
                    parent = family_member.parent
                    if parent :
                        contacts = EmergencyContact.objects.filter(parent=parent)
                        for contact in contacts:
                            emergency_contacts.append(contact)
                    if parent.fcm_token :
                        token =parent.fcm_token
                        text = f"Vous avez reçu une alerte de votre enfant {device.prenom}."
                        try :
                            send_simple_notification(token,text,"warning_sound")
                        except Exception as e:  # Capturer toutes les exceptions
                            print(f"Erreur lors de l'envoi de la notification à {parent}: {e}")
                    AlertNotification.objects.create(alert=alert,type_notification='alerte', parent=parent)
                for contact in emergency_contacts:
                    text = f"Urgence ! Votre enfant {device.prenom} a besoin de votre attention immédiate. Prenez le temps de vérifier et de rassurer votre enfant."
                    send_sms(contact.phone_number, text)
                return Response({'data': None, 'message': 'Alert created and emergency contacts notified.',"success": True,"code" : 200}, status=status.HTTP_201_CREATED)
            else :
                try:
                    child = Child.objects.filter(slug=slug).first()
                    if not child:
                        return Response({'data': None, 'message': 'Device or Child not found', 'success': True, "code": 404}, status=status.HTTP_404_NOT_FOUND)
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
                                send_simple_notification(token,text,"warning_sound")
                            except Exception as e:  # Capturer toutes les exceptions
                                print(f"Erreur lors de l'envoi de la notification à {parent}: {e}")
                        AlertNotification.objects.create(alert=alert,type_notification='alerte', parent=parent)
                    for contact in emergency_contacts:
                        text = f"Urgence ! Votre enfant {child.prenom} a besoin de votre attention immédiate. Prenez le temps de vérifier et de rassurer votre enfant."
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
            return Response({'data': None, 'message': 'Aucune notification pour ce parent', 'success': True, "code" : 200}, status=status.HTTP_200_OK)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'data': serializer.data, 'message': 'Notifications du parent.', "success": True, "code": 200}, status=status.HTTP_200_OK)


# Ajoue du point de reference pour la perimetre de securiité de l'enfant
class addPointTrajetForChild(generics.CreateAPIView):
    serializer_class = PointTrajetSerializer
    queryset = PointTrajet.objects.all()
    def post(self, request, *args, **kwargs):
        try:
            # Utilise get pour obtenir un seul objet
            parent = Parent.objects.get(id=request.data.get('parent'))
        except Parent.DoesNotExist:
            return Response(
                {
                    'data': None,
                    'message': 'Aucun Parent trouvé pour ce point de référence',
                    'success': False,
                    'code': 404
                }, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PointTrajetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'data': serializer.data,
                    'message': 'Point de référence ajouté avec succès',
                    'success': True,
                    'code': 200
                }, 
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'data': None,
                    'message': serializer.errors,
                    'success': False,
                    'code': 400
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )
# vews pour ajouter un permetre de securté par le parent pour son enfant     
class addPerimetreDeSecurityForChild(generics.CreateAPIView):
    serializer_class = PerimetreaddSecuriteSerializer
    queryset = PerimetreSecurite.objects.all()

    def post(self, request, *args, **kwargs):
        try:
            # Utilise get pour obtenir un seul point_trajet
            point_trajet = PointTrajet.objects.get(id=request.data.get('point_trajet'))
        except PointTrajet.DoesNotExist:
            return Response(
                {
                    'data': None,
                    'message': 'Aucun point de référence trouvé pour ce périmètre de sécurité',
                    'success': False,
                    'code': 404
                }, 
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            enfant = Child.objects.get(id = request.data.get('enfant'))
        except Child.DoesNotExist:
            return Response(
                {
                    'data': None,
                    'message': 'Aucun enfant trouvé pour ce périmètre de sécurité',
                    'success': False,
                    'code': 404
                }, 
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            point_trajet_exist = PerimetreSecurite.objects.filter(enfant=request.data.get('enfant')).first()
        except PerimetreSecurite.DoesNotExist:
            pass
        # j'ai commenter cette partie par ce que maintenant l'enfant peux avoir plusieur perimetre de securité or que au debut c'etait pas le cas l'enfant ne pouvais avoir qu'un seule perimetre de secuirite'
        # if point_trajet_exist:
        #     point_trajet_exist.delete()
        serializer = PerimetreaddSecuriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'data': serializer.data,
                    'message': 'Périmètre de sécurité ajouté avec succès',
                    'success': True,
                    'code': 200
                }, 
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'data': None,
                    'message': serializer.errors,
                    'success': False,
                    'code': 400
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )


class tesspositionEnfantInZone(generics.CreateAPIView):
    serializer_class = ChildSerializer
    queryset = Child.objects.all()

    def post(self, request, *args, **kwargs):
        # Récupérer le pk de l'enfant depuis l'URL
        slug = kwargs.get('slug')
        
        # Coordonnées de l'enfant (par exemple, Dakar)
        lat_enfant = 14.6928
        lon_enfant =  -17.4467
        
        # Appeler la fonction pour vérifier la position de l'enfant dans la zone
        resultat = verifier_enfant_dans_zone(slug, lat_enfant, lon_enfant)
        print("la response qui devrai etre retourner")
        print(resultat)
        # Retourner le résultat en réponse JSON
        return resultat
    
# views pour modifier ou suprimé un perimetre de securité
class PerimetreSecuriteView(generics.CreateAPIView):
    serializer_class = PerimetreSecuriteSerializer
    queryset = PerimetreSecurite.objects.all()

    def get(self, request, slug, *args, **kwargs):
        try:
            perimetre_securite = PerimetreSecurite.objects.filter(enfant__slug=slug)
            serializer = PerimetreSecuriteSerializer(perimetre_securite,many=True)
            return Response({
                'data': serializer.data,
                'message': 'Périmètre de sécurité trouvé avec succès',
                'success': True,
                'code': 200
            }, status=status.HTTP_200_OK)
        except PerimetreSecurite.DoesNotExist:
            return Response({
                'data': None,
                'message': 'Aucun périmètre de sécurité trouvé pour cet enfant',
                'success': False,
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, slug, *args, **kwargs):
        try:
            perimetre_securite = PerimetreSecurite.objects.get(slug=slug)
            serializer = PerimetreSecuriteSerializer(perimetre_securite, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'data': serializer.data,
                    'message': 'Périmètre de sécurité modifié avec succès',
                    'success': True,
                    'code': 200
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'data': None,
                    'message': serializer.errors,
                    'success': False,
                    'code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
        except PerimetreSecurite.DoesNotExist:
            return Response({
                'data': None,
                'message': 'Aucun périmètre de sécurité trouvé pour cet enfant',
                'success': False,
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, slug, *args, **kwargs):
        try:
            perimetre_securite = PerimetreSecurite.objects.get(slug=slug)
            perimetre_securite.delete()
            return Response({
                'message': 'Périmètre de sécurité supprimé avec succès',
                'success': True,
                'code': 204
            }, status=status.HTTP_204_NO_CONTENT)
        except PerimetreSecurite.DoesNotExist:
            return Response({
                'data': None,
                'message': 'Aucun périmètre de sécurité trouvé pour cet enfant',
                'success': False,
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
# views pour lister modifier ou supprimer le perimetre de securité
class PointDeReferenceViews(generics.CreateAPIView):
    serializer_class = PointTrajetSerializer
    queryset = PointTrajet.objects.all()

    def get(self, request, slug, *args, **kwargs):
        try:
            point_trajet = PointTrajet.objects.filter(parent__slug=slug)
            serializer = PointTrajetSerializer(point_trajet, many=True)
            return Response({
                'data': serializer.data,
                'message': 'Point trajet listé avec succès',
                'success': True,
                'code': 200
            }, status=status.HTTP_200_OK)
        except PointTrajet.DoesNotExist:
            return Response({
                'data': None,
                'message': 'Aucun point trajet trouvé pour ce parent',
                'success': False,
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, slug, *args, **kwargs):
        try:
            point_trajet = PointTrajet.objects.get(slug=slug)
            serializer = PointTrajetSerializer(point_trajet, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'data': serializer.data,
                    'message': 'Point trajet modifié avec succès',
                    'success': True,
                    'code': 200
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'data': None,
                    'message': serializer.errors,
                    'success': False,
                    'code': 400
                }, status=status.HTTP_400_BAD_REQUEST)
        except PointTrajet.DoesNotExist:
            return Response({
                'data': None,
                'message': 'Aucun point trajet trouvé pour ce slug',
                'success': False,
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, slug, *args, **kwargs):
        try:
            point_trajet = PointTrajet.objects.get(slug=slug)
            point_trajet.delete()
            return Response({
                'message': 'Point trajet supprimé avec succès',
                'success': True,
                'code': 204
            }, status=status.HTTP_204_NO_CONTENT)
        except PointTrajet.DoesNotExist:
            return Response({
                'message': 'Aucun point trajet trouvé pour la suppression',
                'success': False,
                'code': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
# Une views pour permetre au parent de pouvoir activer ou desactiver un point perimetre de securité dont un doit etre activer
class AnabledOrDisabledPerimetreDesecurite(generics.CreateAPIView):
    serializer_class = PerimetreaddSecuriteSerializer
    queryset = PerimetreSecurite.objects.all()

    def put(self, request, slug, *args, **kwargs):
        try:
            perimetre_securite = PerimetreSecurite.objects.get(slug=slug)
        except PerimetreSecurite.DoesNotExist:
            return Response({"data": None,"message": "Aucun périmètre de sécurité trouvé","success": False,"code": 404}, status=status.HTTP_404_NOT_FOUND)

        if perimetre_securite.is_active:

            perimetre_securite.is_active = False
            perimetre_securite.save()
            return Response({ "data": None,"message": "Périmètre de sécurité désactivé avec succès","success": True,"code": 200}, status=status.HTTP_200_OK)

        # Vérifier si un autre périmètre actif existe pour cet enfant
        child = perimetre_securite.enfant
        if PerimetreSecurite.objects.filter(enfant=child, is_active=True).exists():
            return Response({"data": None,"message": "Veuillez désactiver tous les points actifs avant d'en activer un autre","success": False,"code": 400}, status=status.HTTP_400_BAD_REQUEST)

        # Activer le périmètre si aucun autre n'est actif
        perimetre_securite.is_active = True
        perimetre_securite.save()
        return Response({"data": None,"message": "Périmètre de sécurité activé avec succès", "success": True,"code": 200}, status=status.HTTP_200_OK)

        

# Views pour que le parent puis accepter ou rejeter une demande de co-parent
class ParentAcceptedOrDismissRequest(generics.ListCreateAPIView):
    queryset = Demande.objects.all()
    serializer_class = DemandeSerializer
    def put(self, request, *args, **kwargs):
        slug_notification = request.data.get('slug_notification','')
        status_notification = request.data.get('status_notification','')
        # Verifier  si la notification est lier a un demande et recupperer la demande
        try:
            notification = AlertNotification.objects.filter(slug=slug_notification).last()
            demande =Demande.objects.get(notification=notification)
        except Demande.DoesNotExist:
            return Response({"data": None, "message": "Aucune demande trouver pour ce notification", "success":False}, status=status.HTTP_404_NOT_FOUND)
        # tester si le premier parent accepte la demande de lier l'enfant et le co-parent on envoie des notifications au co-parent et creer le family member
        if status_notification == "Accepté":

            family_member = FamilyMember.objects.create(relation=demande.relationship,parent=demande.parent,child=demande.enfant)
            notification.status = "Accepté"
            notification.save()
            demande.status = "Accepté"
            demande.save()
            back_notification = AlertNotification(type_notification="demande", parent=demande.parent,status="Accepté")
            if demande.parent.fcm_token :
                token =demande.parent.fcm_token
                text = f"Bonne nouvelle ! Votre demande pour devenir co-parent de l'enfant  {demande.enfant.prenom} {demande.enfant.nom} a été acceptée par {demande.parent.prenom} {demande.parent.nom}.Ensemble, vous construisez un environnement plus sûr pour cet enfant."
                try :
                    send_simple_notification(token,text)
                except Exception as e:  # Capturer toutes les exceptions
                    print(f"Erreur lors de l'envoi de la notification à {demande}: {e}")
            if demande.parent.phone_number:
                phone_number = demande.parent.phone_number
                text = f"Bonne nouvelle ! Votre demande pour devenir co-parent de l'enfant  {demande.enfant.prenom} {demande.enfant.nom} a été acceptée par {demande.parent.prenom} {demande.parent.nom}.Ensemble, vous construisez un environnement plus sûr pour cet enfant."
                send_sms(phone_number, text)
            serializer = DemandeSerializer(demande)
            return Response({"data": serializer.data, "message" : "Demande accepté avec succées", "status" : True , "code" : 200},status=status.HTTP_200_OK)
        else:
            back_notification = AlertNotification(type_notification="demande", parent=demande.parent,status="Refusé")
            notification.status = "Refusé"
            notification.save()
            demande.status = "Refusé"
            demande.save()
            if demande.parent.fcm_token :
                token =demande.parent.fcm_token
                text = f"Votre demande pour devenir co-parent de l'enfant    {demande.enfant.prenom} {demande.enfant.nom} a été refusée par {demande.parent.prenom} {demande.parent.nom}.Nous vous encourageons à communiquer avec le parent principal pour en discuter."
                try :
                    send_simple_notification(token,text)
                except Exception as e:  # Capturer toutes les exceptions
                    print(f"Erreur lors de l'envoi de la notification à {demande}: {e}")
            if demande.parent.phone_number:
                phone_number = demande.parent.phone_number
                text = f"Votre demande pour devenir co-parent de l'enfant    {demande.enfant.prenom} {demande.enfant.nom} a été refusée par {demande.parent.prenom} {demande.parent.nom}.Nous vous encourageons à communiquer avec le parent principal pour en discuter."
                send_sms(phone_number, text)
            serializer = DemandeSerializer(demande)
            return Response({"data" : serializer.data, "message" : "Demande rejété avec succées", "status" : True, "code" : 200}, status=status.HTTP_200_OK)
        
# views pour la detaille de demande l'or de la validation de la demande par le parent
class DetailDemandeForNotification(generics.RetrieveAPIView):
    serializer_class = DetailDemandeSerializer()
    queryset = Demande.objects.all()
    def get(self, request, slug, *args, **kwargs):
        slug = self.kwargs.get('slug')
        try:
            demande = Demande.objects.filter(notification__slug=slug).last()
        except Demande.DoesNotExist:
            return Response({"data" : None, "message" : "Aucune Demande trouver pour cette notification", "success" : False, "code" : 400}, status=status.HTTP_404_NOT_FOUND)
        serializer = DetailDemandeSerializer(demande)
        return Response({"data" : serializer.data , "message" : "détail demande" , "success" : True, "code" :200} , status=status.HTTP_200_OK)


# Cette views vas juste nous permetre de retourner les enfant d'un parent
class GetAllChildForthisParent(generics.ListAPIView):
    serializer_class = FamilyMemberSerializer()
    queryset = FamilyMember.objects.all()
    def get(self, request, slug, *args,**kwargs):
        try:
            family_members = FamilyMember.objects.filter(parent__slug=slug)
        except FamilyMember.DoesNotExist:
            return Response({"data" : None, "message" : "Ce parent n'est lié à aucun enfant", "access" : True, "code" : 200}, status=status.HTTP_200_OK)
        if family_members:
            children = [family_member.child for family_member in family_members]
            serializer = ChildSerializer(children, many=True)
            return Response({"data" : serializer.data , "message" : "Liste des enfants", "access" : True, "code" : 200}, status=status.HTTP_200_OK)
        else:
            return Response({"data" : None, "message" : "Ce parent n'est lié à aucun enfant", "access" : True, "code" : 200}, status=status.HTTP_200_OK)

        
# Le nouveau process pour creer un perimetre de securité par le parent et la liesons d'un perimetre de securité a un enfant
class ParentAddPerimetreOfSecurity(generics.CreateAPIView):
    serializer_class = PerimetreaddSecuriteSerializer
    queryset = PerimetreSecurite.objects.all()

    def post(self, request, *args, **kwargs):
        slug_parent = request.data.get('slug_parent')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        # Vérification de l'existence du parent
        try:
            parent = Parent.objects.get(slug=slug_parent)
        except Parent.DoesNotExist:
            return Response(
                {
                    "data": None,
                    "message": "Le parent n'existe pas",
                    "success": False,
                    "code": 400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Vérification des coordonnées
        if not latitude or not longitude:
            return Response(
                {
                    "data": None,
                    "message": "La latitude et la longitude sont obligatoires",
                    "success": False,
                    "code": 400,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Ajout du parent aux données avant la sérialisation
        request.data['parent'] = parent.id
        # Sérialisation et validation des données
        serializer = PerimetreaddSecuriteSerializer(data=request.data)
        if serializer.is_valid():
            perimetre = serializer.save()
            return Response(
                {
                    "data": PerimetreaddSecuriteSerializer(perimetre).data,
                    "message": "Périmètre de sécurité créé avec succès",
                    "success": True,
                    "code": 201,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "data": serializer.errors,
                "message": "Une erreur s'est produite",
                "success": False,
                "code": 400,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

# Relier un perimetre de securité a un enfant pour la verification
class ConnectChildSafetyPerimeter(generics.CreateAPIView):
    serializer_class = ChildWithPerimetreSecuriteSerializer
    queryset = ChildWithPerimetreSecurite.objects.all()

    def post(self, request, *args, **kwargs):
        perimetre_slug = request.data.get("perimetre_slug")
        child_slug = request.data.get("child_slug")

        try:
            perimetre = PerimetreSecurite.objects.get(slug=perimetre_slug)
        except PerimetreSecurite.DoesNotExist:
            return Response(
                {"data": None, "message": "Le périmètre de sécurité n'existe pas", "success": False, "code": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        child = None
        device = None

        try:
            child = Child.objects.get(slug=child_slug)
        except Child.DoesNotExist:
            pass

        try:
            device = Device.objects.get(slug=child_slug)
        except Device.DoesNotExist:
            pass

        if child:
            child_with_psec = ChildWithPerimetreSecurite.objects.filter(
                child=child, perimetre_securite=perimetre, is_active=True
            ).first()
        elif device:
            child_with_psec = ChildWithPerimetreSecurite.objects.filter(
                device=device, perimetre_securite=perimetre, is_active=True
            ).first()
        else:
            return Response({
                "data": None,
                "message": "Enfant ou appareil non trouvé",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        

        if child_with_psec:
            child_with_psec.is_active = False
            child_with_psec.save()
            return Response(
                {
                    "data": ChildWithPerimetreSecuriteSerializer(child_with_psec).data,
                    "message": "Périmètre de sécurité désactivé avec succès",
                    "success": True,
                    "code": 200,
                },
                status=status.HTTP_200_OK,
            )
        # Désactiver tous les anciens périmètres de l'enfant
        ChildWithPerimetreSecurite.objects.filter(child=child).update(is_active=False)

        # Activer ou créer l'association entre l'enfant et le périmètre
        child_with_perimetre, created = ChildWithPerimetreSecurite.objects.update_or_create(
            child=child,device=device, perimetre_securite=perimetre, defaults={"is_active": True}
        )

        message = "Périmètre de sécurité activé avec succès" if not created else "Périmètre de sécurité affecté avec succès"
        
        return Response(
            {
                "data": ChildWithPerimetreSecuriteSerializer(child_with_perimetre).data,
                "message": message,
                "success": True,
                "code": 200 if not created else 201,
            },
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
        )
    
# Lister les perimetre de securité d'un parent vec les enfant 
class ParentPerimetreListView(generics.ListAPIView):
    def get(self, request, slug, *args, **kwargs):
        parent = get_object_or_404(Parent, slug=slug)  
        perimetres = PerimetreSecurite.objects.filter(parent=parent)
        
        serializer = ListePerimetreSecuriteSerializer(perimetres, many=True)

        return Response(
            {"data": serializer.data, "message": "Périmètres de sécurité du parent récupérés", "success": True, "code": 200},
            status=status.HTTP_200_OK
        )
    

# liste des perimetre de securité pour l'enfzntclass 
class ChildPerimetreListView(generics.ListAPIView):
    def get(self, request, slug, *args, **kwargs):
        child = None
        device = None

        try:
            child = Child.objects.get(slug=slug)
        except Child.DoesNotExist:
            pass

        try:
            device = Device.objects.get(slug=slug)
        except Device.DoesNotExist:
            pass

        if child:
            perimetres_associes = ChildWithPerimetreSecurite.objects.filter(child=child)
        elif device:
            perimetres_associes = ChildWithPerimetreSecurite.objects.filter(device=device)
        else:
            return Response({
                "data": None,
                "message": "Enfant ou appareil non trouvé",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

        # Sérialiser l'enfant une seule fois
        child_serializer = ChildSerializer(child)

        # Sérialiser les périmètres associés
        perimetres_serializer = PerimetreAssocieSerializer(perimetres_associes, many=True)

        return Response(
            {
                "child": child_serializer.data,  # L'enfant une seule fois
                "perimetres": perimetres_serializer.data,  # Liste des périmètres
                "message": "Périmètres de l'enfant récupérés",
                "success": True,
                "code" : 200
            },
            status=status.HTTP_200_OK)
        