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
import base64
from django.utils.translation import gettext as _
from django.db.utils import IntegrityError
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView


# Instancier un logger
logger = logging.getLogger(__name__)
class AddDevice(generics.CreateAPIView):
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()

    def post(self, request, *args, **kwargs):
        logger.info("📩 Requête POST reçue pour ajout de device")
        logger.debug(f"Données reçues : {request.data}")

        child_slug = request.data.get("child_slug")
        child = None

        if child_slug:
            try:
                child = Child.objects.get(slug=child_slug)
                logger.info(f"Enfant trouvé : {child.slug}")
            except Child.DoesNotExist:
                logger.warning(f"Aucun enfant trouvé pour le slug : {child_slug}")
                return Response({
                    "data": None,
                    "message": "Aucun enfant trouvé",
                    "success": False,
                    "code": 404
                }, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        if child:
            data["child"] = child.id

        serializer = self.get_serializer(data=data)

        if serializer.is_valid():
            serializer.save()
            logger.info(f"Device ajouté avec succès : {serializer.data}")
            return Response({
                "data": serializer.data,
                "message": "Device ajouté avec succès",
                "success": True,
                "code": 201
            }, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"Erreurs de validation : {serializer.errors}")
            return Response({
                "data": serializer.errors,
                "message": "Erreur de validation",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)


# methode pour stocker les données de la batery du dice
class BatteryStatusSave(generics.CreateAPIView):
    serializer_class = SerializerBatteryStatus
    queryset = BatteryStatus.objects.all()

    def post(self, request, *args, **kwargs):
        device_identity = request.data.get("device")
        battery = request.data.get("battery")
        try:
            device = Device.objects.get(imei=device_identity)
        except Device.DoesNotExist:
            return Response({
                "data": None,
                "message": "Aucun device trouvé",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data["device"] = device.id

        serializer = SerializerBatteryStatus(data=data)
        if serializer.is_valid():
            serializer.save()
            device.battery_level = battery
            device.save()
            return Response({
                "data": serializer.data,
                "message": "Status de la batterie bien mis à jour",
                "success": True,
                "code": 201
            }, status=status.HTTP_201_CREATED)

        return Response({
            "data": serializer.errors,
            "message": "Erreur de validation des données",
            "success": False,
            "code": 400
        }, status=status.HTTP_400_BAD_REQUEST)
class WellStockFamilyNumberForDevice(generics.CreateAPIView):
    serializer_class = FamilyNumberSerializer
    queryset = FamilyNumber.objects.all()

    def post(self, request, *args, **kwargs):
        device_identity = request.data.get("device_identity")

        if not device_identity:
            return Response({
                "data": None,
                "message": "Veuillez fournir un identifiant de device",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.get(imei=device_identity)
        except Device.DoesNotExist:
            return Response({
                "data": None,
                "message": "Device introuvable",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

        number = request.data.get("number")

        # Vérifier si le numéro est déjà enregistré pour ce device
        if FamilyNumber.objects.filter(device=device, number=number).exists():
            return Response({
                "data": None,
                "message": "Ce numéro est déjà enregistré pour ce device",
                "success": False,
                "code": 409
            }, status=status.HTTP_409_CONFLICT)

        # Vérifier qu'on n'a pas déjà 3 numéros
        existing = FamilyNumber.objects.filter(device=device)
        if existing.count() >= 3:
            return Response({
                "data": None,
                "message": "Limite de 3 numéros atteinte pour ce device",
                "success": False,
                "code": 403
            }, status=status.HTTP_403_FORBIDDEN)

        # Trouver le serialnumber libre (0, 1 ou 2)
        used_serials = existing.values_list("serialnumber", flat=True)
        for i in range(3):
            if i not in used_serials:
                serialnumber = i
                break

        # Générer automatiquement le nom en fonction du serialnumber
        names = {0: "111", 1: "2222", 2: "3333"}
        name = names.get(serialnumber)

        data = {
            "device": device.id,
            "number": number,
            "serialnumber": serialnumber,
            "name": name
        }

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "data": serializer.data,
                "message": "Numéro enregistré avec succès",
                "success": True,
                "code": 201
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "data": serializer.errors,
                "message": "Erreur de validation",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)
class bateriestatusList(generics.ListAPIView):
    serializer_class = SerializerBatteryStatus
    queryset = BatteryStatus.objects.all()
    def get(self,slug, request, *args, **kwargs):
        try:
            device = Device.objects.get(slug=slug)
        except Device.DoesNotExist:
            return Response({
                "data": None,
                "message": "Aucun device trouver",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        baterie = BatteryStatus.objects.filter(device=device).last()
        serializer = SerializerBatteryStatus(baterie)
        return Response({
            "data": serializer.data,
            "message": "Derniere stat de baterie lister avec succées",
            "success": True,
            "code": 201
        }, status=status.HTTP_201_CREATED)
        
        
        
        
# Methode pour retourner les numero pour le divice
class FamilyNumberView(APIView):
    def post(self, request):
        identity = request.data.get("identity")
        type_value = request.data.get("type")

        if not identity or str(type_value) != "5":
            return Response({
                "success": False,
                "message": "Invalid identity or type"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.get(imei=identity)
        except Device.DoesNotExist:
            return Response({
                "success": False,
                "message": "Device not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # 📦 Récupérer les numéros existants
        existing_numbers = {
            fn.serialnumber: fn
            for fn in device.family_numbers.all()
        }

        #Mapping fixe des noms selon le numéro
        name_map = {0: "111", 1: "2222", 2: "3333"}

        #Construire la réponse avec les 3 cases (0,1,2)
        familyNumber = []
        for i in range(3):
            fn = existing_numbers.get(i)
            if fn:
                familyNumber.append({
                    "number": fn.number,
                    "serialnumber": str(i),
                    "name": name_map[i],
                    "url": fn.url
                })
            else:
                familyNumber.append({
                    "number": "",
                    "serialnumber": str(i),
                    "name": name_map[i],
                    "url": None
                })

        return Response({
            "success": True,
            "familyNumber": familyNumber,
            "message": "Operation Successfully"
        }, status=status.HTTP_200_OK)
        
        
        
class GeolocaliserParWifiMozilla(APIView):
    def post(self, request):
        """
        POST attendu :
        {
            "wifi_data": "mac,-strength,ssid|mac,-strength,ssid|..."
        }
        """
        wifi_data_str = request.data.get("wifi_data")

        if not wifi_data_str:
            return Response({
                "success": False,
                "message": "wifi_data est requis",
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        # 🔧 Parse du wifi_data
        wifi_data = []
        try:
            points = wifi_data_str.split("|")
            for point in points:
                parts = point.split(",")
                if len(parts) >= 2:
                    mac = parts[0].strip()
                    strength = int(parts[1].strip())
                    wifi_data.append({"macAddress": mac, "signalStrength": strength})
        except Exception as e:
            return Response({
                "success": False,
                "message": f"Erreur lors de l'analyse : {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 🌍 Appel Mozilla Location Service
        url = "https://location.services.mozilla.com/v1/geolocate?key=test"
        payload = {"wifiAccessPoints": wifi_data}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            return Response({
                "success": True,
                "latitude": result['location']['lat'],
                "longitude": result['location']['lng'],
                "accuracy": result.get('accuracy'),
                "message": "Position récupérée avec succès"
            }, status=status.HTTP_200_OK)

        except requests.exceptions.HTTPError as http_err:
            return Response({
                "success": False,
                "error": f"Erreur HTTP: {http_err}",
                "details": response.text
            }, status=status.HTTP_502_BAD_GATEWAY)

        except Exception as e:
            return Response({
                "success": False,
                "error": f"Erreur interne : {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

# Cette fonction permet juste d'ajouter des serial number pour les bouton du device
def registerFamilyNumberForDevice(number,device_identity):

        if not device_identity:
            return Response({
                "data": None,
                "message": "Veuillez fournir un identifiant de device",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.get(imei=device_identity)
        except Device.DoesNotExist:
            return Response({
                "data": None,
                "message": "Device introuvable",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

        # Vérifier si le numéro est déjà enregistré pour ce device
        if FamilyNumber.objects.filter(device=device, number=number).exists():
            return Response({
                "data": None,
                "message": "Ce numéro est déjà enregistré pour ce device",
                "success": False,
                "code": 409
            }, status=status.HTTP_409_CONFLICT)

        # Vérifier qu'on n'a pas déjà 3 numéros
        existing = FamilyNumber.objects.filter(device=device)
        if existing.count() >= 3:
            return Response({
                "data": None,
                "message": "Limite de 3 numéros atteinte pour ce device",
                "success": False,
                "code": 403
            }, status=status.HTTP_403_FORBIDDEN)

        # Trouver le serialnumber libre (0, 1 ou 2)
        used_serials = existing.values_list("serialnumber", flat=True)
        for i in range(3):
            if i not in used_serials:
                serialnumber = i
                break

        # Générer automatiquement le nom en fonction du serialnumber
        names = {0: "111", 1: "2222", 2: "3333"}
        name = names.get(serialnumber)

        data = {
            "device": device.id,
            "number": number,
            "serialnumber": serialnumber,
            "name": name
        }

        serializer = FamilyNumberSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "data": serializer.data,
                "message": "Numéro enregistré avec succès",
                "success": True,
                "code": 201
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "data": serializer.errors,
                "message": "Erreur de validation",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

class ReleaseParentToDevice(generics.CreateAPIView):
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()

    def post(self, request, *args, **kwargs):
        numbers = request.data.get("numbers")
        emei = request.data.get("imei")
        nom = request.data.get("nom")
        prenom = request.data.get("prenom")
        slug_parent = request.data.get("slug_parent")
        relation = request.data.get("relation")
        phone_number = request.data.get("phone_number")

        if not emei or not slug_parent:
            return Response({
                "data": None,
                "message": "Identifiants manquants (imei ou slug_parent)",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            parent = Parent.objects.get(slug=slug_parent)
        except Parent.DoesNotExist:
            return Response({
                "data": None,
                "message": "Aucun parent trouvé pour cet identifiant",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
        try:
            device = Device.objects.get(imei=emei)
        except Device.DoesNotExist:
            return Response({
                "data": None,
                "message": "Aucun device trouvé pour cet identifiant",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

        # Vérifier si déjà lié
        famille = FamilyMember.objects.filter(device=device).first()
        if famille:
            slug=device.slug
            return self.handle_new_parent_request(device, slug_parent, relation, slug, request)

        # Créer le lien famille
        family_member = FamilyMember.objects.create(
            relation=relation,
            parent=parent,
            device=device
        )

        # Mettre à jour les infos du device
        device.nom = nom
        device.prenom = prenom
        device.phone_number = phone_number
        device.save()

        # Enregistrer les numéros associés
        if numbers:
            for number in numbers:
                registerFamilyNumberForDevice(number, emei)

        # Sérialisation
        serialized_data = FamilyMemberSerializer(family_member).data

        return Response({
            "data": serialized_data,
            "message": "Information enregistrée avec succès. Le parent peut suivre l'enfant à partir du device.",
            "success": True,
            "code": 200
        }, status=status.HTTP_200_OK)
        


    def handle_new_parent_request(self, device, slug_parent, relation, slug, request):
        """Envoyer une demande de co-parenting au parent principal."""
        exists = FamilyMember.objects.filter(parent__slug=slug_parent, device__slug=slug).exists()
        if exists:
            return Response({
                "data": None,
                "message": "Vous avez déjà une relation de parenté avec cet enfant.",
                "access": False,
                "code": "400"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            parent = Parent.objects.get(slug=slug_parent)
        except Parent.DoesNotExist:
            return Response({
                'data': None,
                'message': "Aucun parent trouvé pour la création du compte de l'enfant",
                'success': False
            }, status=status.HTTP_400_BAD_REQUEST)

        first_family_member = FamilyMember.objects.filter(device=device).order_by('created_at').first()

        comment = f"Un nouveau parent souhaite ajouter {device.prenom} {device.nom}."
        notification = AlertNotification.objects.create(type_notification="demande", parent=first_family_member.parent, comment=comment)
        Demande.objects.create(
            device=device,
            parent=parent,
            parent_recepteur=first_family_member.parent,
            relationship=relation,
            notification=notification
        )

        # Message unique pour notification et SMS
        message_text = f"Bonjour {parent.prenom} {parent.nom} a exprimé le souhait de devenir co-parent pour votre enfant {device.prenom} {device.nom}. Votre décision est essentielle pour renforcer le cercle de protection de votre enfant."

        if first_family_member.parent.fcm_token:
            try:
                send_simple_notification(first_family_member.parent.fcm_token, message_text)
            except Exception as e:
                print(f"Erreur lors de l'envoi de la notification : {e}")

        if first_family_member.parent.phone_number:
            send_sms(first_family_member.parent.phone_number, message_text)

        return Response({
            "data": ParentSerializer(first_family_member.parent).data,
            "message": f"Merci d'attendre l'approbation du parent {first_family_member.parent.prenom} {first_family_member.parent.nom}",
            "success": True,
            "code": 200
        }, status=status.HTTP_200_OK)
        
class AddDevicePhoto(generics.CreateAPIView):
    serializer_class = DevicePhotoSerializer

    def post(self, request, *args, **kwargs):
        imei      = request.data.get('device')
        timestamp = request.data.get('timestamp')
        image     = request.FILES.get('image')

        if not imei:
            return Response({
                "data": None,
                "message": "IMEI du device requis",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        if not image:
            return Response({
                "data": None,
                "message": "Image requise",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.get(imei=imei)
        except Device.DoesNotExist:
            return Response({
                "data": None,
                "message": "Aucun device trouvé avec cet IMEI",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        photo = DevicePhoto.objects.create(
            device=device,
            image=image,
            timestamp=timestamp or "",
        )

        return Response({
            "data": {
                "id": photo.pk,
                "slug": str(photo.slug),
                "device": device.pk,
                "timestamp": photo.timestamp,
                "captured_at": photo.captured_at,
                "image_url": request.build_absolute_uri(photo.image.url),
            },
            "message": "Photo enregistrée avec succès",
            "success": True,
            "code": 201
        }, status=status.HTTP_201_CREATED)