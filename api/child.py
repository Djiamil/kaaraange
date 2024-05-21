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


# la views pour creer le Child temporelement en attendant qu'il valide otp
class RegisterChild(generics.CreateAPIView):
    queryset = PendingUser.objects.all()
    serializer_class = PendingUserGetSerializer

    def get(self, request, *args, **kwargs):
        child = Child.objects.all()
      
        serializer = UserSerializer(child, many=True)
        return Response({'data' : {'child':serializer.data}, 'message' : "Chld liste", 'success' : True, 'code' : 200},status.HTTP_201_CREATED)
    def post(self, request, *args, **kwargs):
        serializer = PendingUserGetSerializer(data=request.data)
        if serializer.is_valid():
            pendingUser = serializer.save()
            otp_code = generate_otp(pendingUser)
            to_phone_number = request.data['telephone']
            text = "Veillez recevoir votre code de confirmation d'inscription " + otp_code
            send_sms(to_phone_number, text)
            response_serializer = PendingUserGetSerializer(pendingUser)
            return Response({
                "data" : {
                    "child" : response_serializer.data
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
# views pour l'inscription de l'enfant 
class ConfirmRegistrationChild(generics.CreateAPIView):
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
        child = Child.objects.create(
            email = pending_user.email,
            phone_number = pending_user.telephone,
            prenom=pending_user.prenom,
            nom = pending_user.nom,
            date_de_naissance = pending_user.date_de_naissance,
            password=make_password(pending_user.password),
            accepted_terms = True,
            gender = pending_user.gender,
            allergies = pending_user.allergies ,
            ecole = pending_user.ecole,
            user_type = 'CHILD'
            )
        qr_image = generate_qrcode_image(child)
        parent_child_link = ParentChildLink.objects.create(child=child, qr_code=qr_image)
        serializer = ChildSerializerDetail(child)
        if qr_image:
            qr_base64 = base64.b64encode(qr_image).decode('utf-8')
        pending_user.delete()
        otp.delete()
        return Response({
            "data" : {
                'child' : serializer.data,
                'qr_base64' : qr_base64
            },
            "message": 'Compte utilisateur créé avec succès',
            "success" : True,
            "code" : 200,
            }, status=status.HTTP_201_CREATED)
# permet de relier le parent a l'nfant  dans le model parent link to child
class ParendChildLink(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        slug_child = request.data.get('slug_child', None)
        slug_parent = request.data.get('slug_parent', None)
        relation = request.data.get('relation', None)
                # Vérifier si la relation est valide
        valid_relations = [choice[0] for choice in FamilyMember.RELATIONSHIP_CHOICES]
        if relation not in valid_relations:
            return Response({
                "data": None,
                "message": "La relation spécifiée n'est pas valide",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)
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
                        return Response({
                            "dada" :None,
                            "message" : 'Parents ajoutés avec succès à l\'enfant',
                            "success" : True,
                            "code" : 200,
                        }, status=200)
                    else:
                        return Response({
                            "data" : None,
                            "message" : "Cette enfant a deja cette type de  relaton",
                            "success" : False,
                            "code" : 400
                        }, status=400)
                    
                except IntegrityError:
                    return Response({
                        "data" : None,
                        "message" : 'Cette enfant a deja cette type de  relaton',
                        "success" : False,
                        "code" : 400
                        }, status=400)
                
            except Child.DoesNotExist:
                return Response({
                    "data" : None,
                    "message" : 'Aucun enfant trouvé avec ce slug',
                    "success" : False,
                    "code" : 404
                }, status=404)
            except Parent.DoesNotExist:
                return Response({
                    "data" : None,
                    "message" : 'Aucun enfant trouvé avec ce slug',
                    "success" : False,
                    "code" : 404
                }, status=404)
        else:
            return Response({
                "data" : None,
                "message" : 'Slug non fourni',
                "success" : False,
                "code" : 400
            }, status=400)

# views pour retourner tous les informations de l'utilisateur enfant pour son dashbord
class childDashbord(generics.RetrieveAPIView):
    queryset = Child.objects.all()
    serializer_class = ChildSerializerDetail
    lookup_field = 'slug'

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        child = get_object_or_404(Child, slug=slug)
        return Response({
            "data" : {
                "child": ChildSerializerDetail(child).data
            },
            'message': 'Detail for child',
            'success': True,
            'code' : 200
            } , status=status.HTTP_200_OK)

