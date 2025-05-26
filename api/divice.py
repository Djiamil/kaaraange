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
            
        
