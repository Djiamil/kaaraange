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


# views pour l'inscription de l'enfant
class ChildRegister(generics.CreateAPIView):
    queryset = Child.objects.all()
    serializer_class = ChildSerializer
    
    def get(self, request, *args, **kwargs):
        children = Child.objects.all()
        serializer = ChildSerializerDetail(children, many=True)
        return Response(serializer.data)
        
    def post(self, request, *args, **kwargs):
        request.data["user_type"] = "CHILD"
        request.data["accepted_terms"] = True
        password = request.data.get('password')
        hashed_password = make_password(password)
        request.data['password'] = hashed_password

        serializer = ChildSerializer(data=request.data)
        if serializer.is_valid(): 
            child = serializer.save()
            qr_image = generate_qrcode_image(child)
            parent_child_link = ParentChildLink.objects.create(child=child, qr_code=qr_image)
            if qr_image:
                qr_base64 = base64.b64encode(qr_image).decode('utf-8')
                return Response({"qr_code": qr_base64}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "Une erreur s'est produite lors de la création du QR code"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# permet de relier le parent a l'nfant  dans le model parent link to child
class ChildDetails(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        slug = request.data.get('slug', None)
        if slug:
            try:
                child = Child.objects.get(slug=slug)
                # Recherche de l'objet ParentChildLink associé à l'enfant
                try:
                    parent_child_link = ParentChildLink.objects.get(child=child)
                    # Mettre à jour l'objet ParentChildLink avec les parents de l'enfant
                    parent_child_link.parent.add(*request.user.parents.all())
                    return Response({'success': 'Parents ajoutés avec succès à l\'enfant'})
                except ParentChildLink.DoesNotExist:
                    return Response({'error': 'Aucun ParentChildLink trouvé pour cet enfant'}, status=404)
            except Child.DoesNotExist:
                return Response({'error': 'Aucun enfant trouvé avec ce slug'}, status=404)
        else:
            return Response({'error': 'Slug non fourni'}, status=400)
