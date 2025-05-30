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



class AddDevice(generics.CreateAPIView):
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()

    def post(self, request, *args, **kwargs):
        child_slug = request.data.get("child_slug")
        child = None

        if child_slug:
            try:
                child = Child.objects.get(slug=child_slug)
            except Child.DoesNotExist:
                return Response({
                    "data": None,
                    "message": "Aucun enfant trouvé",
                    "success": False,
                    "code": 404
                }, status=status.HTTP_404_NOT_FOUND)

        # Création du device avec ou sans enfant
        data = request.data.copy()
        if child:
            data["child"] = child.id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "data": serializer.data,
                "message": "Device ajouté avec succès",
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


# methode pour stocker les données de la batery du dice
class BatteryStatusSave(generics.CreateAPIView):
    serializer_class = SerializerBatteryStatus
    queryset = BatteryStatus.objects.all()

    def post(self, request, *args, **kwargs):
        device_identity = request.data.get("device")
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

        # 🧠 Mapping fixe des noms selon le numéro
        name_map = {0: "111", 1: "2222", 2: "3333"}

        # 📋 Construire la réponse avec les 3 cases (0,1,2)
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
        
