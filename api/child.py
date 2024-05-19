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
class ParendChildLink(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        slug_child = request.data.get('slug_child', None)
        slug_parent = request.data.get('slug_parent', None)
        relation = request.data.get('relation', None)
        
        if slug_child:
            try:
                child = Child.objects.get(slug=slug_child)
                parent = Parent.objects.get(slug=slug_parent)  
                
                try:
                    family_member, created = FamilyMember.objects.get_or_create(
                        parent=parent,
                        child=child,
                        relation=relation
                    )
                    if created:
                        return Response({'success': _('Parents ajoutés avec succès à l\'enfant')})
                    else:
                        return Response({'error': _('La relation spécifiée n\'est pas valide')}, status=400)
                    
                except IntegrityError:
                    return Response({'error': _('La relation spécifiée n\'est pas valide')}, status=400)
                
            except Child.DoesNotExist:
                return Response({'error': _('Aucun enfant trouvé avec ce slug')}, status=404)
            except Parent.DoesNotExist:
                return Response({'error': _('Aucun parent trouvé avec ce slug')}, status=404)
        else:
            return Response({'error': _('Slug non fourni')}, status=400)

# views pour retourner tous les informations de l'utilisateur enfant pour son dashbord
class childDashbord(generics.RetrieveAPIView):
    queryset = Child.objects.all()
    serializer_class = ChildSerializerDetail
    lookup_field = 'slug'

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        child = get_object_or_404(Child, slug=slug)
        child_data_list = []  # Renamed variable to avoid conflict

        # Append child data to the list
        child_data_list.append({'child': ChildSerializerDetail(child).data,
                                })
        return Response({'child': child_data_list})

