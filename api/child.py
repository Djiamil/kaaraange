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




# la views pour creer le Child temporelement en attendant qu'il valide otp cette procedre est remplacer par le oveau flow qui fait qe c'est le parent qui inscris l'enfant 
class RegisterChild(generics.CreateAPIView):
    queryset = PendingUser.objects.all()
    serializer_class = PendingUserGetSerializer

    def get(self, request, *args, **kwargs):
        child = Child.objects.all()
      
        serializer = UserSerializer(child, many=True)
        return Response({'data' : {'child':serializer.data}, 'message' : "Chld liste", 'success' : True, 'code' : 200},status.HTTP_201_CREATED)
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
                    "message" : "Un utilisateur avec cette email ou numero de téléphone existe deja",
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
# views pour la modification de l'enfant 
class UpdateChild(generics.UpdateAPIView):
    queryset = Child.objects.all()
    serializer_class = ChildSerializer
    lookup_field = 'slug'

    def put(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        try:
            child = Child.objects.get(slug=slug)
        except Child.DoesNotExist:
            return Response({
                "data": None,
                "message": "Cet enfant n'existe pas",
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

        serializer = ChildSerializer(child, data=request.data, partial=True)
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


# views pour l'inscription de l'enfant c'est           plus utiliser pour le nouveau flow l'enfant ne recois plus de code otp
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
            avatar = pending_user.avatar,
            date_de_naissance = pending_user.date_de_naissance,
            password=make_password(pending_user.password),
            accepted_terms = True,
            gender = pending_user.gender,
            # allergies = pending_user.allergies ,
            ecole = pending_user.ecole,
            user_type = 'CHILD'
            )
        serializer = ChildSerializerDetail(child)
        pending_user.delete()
        otp.delete()
        return Response({
            "data" : {
                'child' : serializer.data,
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
        parent_child_relation = {}
        try:
            parent_child_relation = FamilyMember.objects.filter(parent__slug=slug_parent,child__slug=slug_child).first()
        except FamilyMember.DoesNotExist:
            pass
        if parent_child_relation :
            return Response({
                "data": None,
                "message": "Cette enfant a deja une relation avec ce parent",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)
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
                        emergencyContact = EmergencyContact.objects.create(
                            parent = parent,
                            phone_number = parent.phone_number,
                            relationship = relation,
                            name = parent.prenom + ' ' + parent.nom
                        )
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
                    "message" : 'Aucun enfant trouvé avec ce qqrcode',
                    "success" : False,
                    "code" : 404
                }, status=404)
            except Parent.DoesNotExist:
                return Response({
                    "data" : None,
                    "message" : 'Aucun enfant trouvé avec ce qrcode',
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


# ajoue de localsations de l'enfant
class AddLocalization(generics.RetrieveAPIView):
    # permission_classes = [IsAuthenticated]
    localisation = Location.objects.all()
    serializer_class = LocationSerializer

    def post(self, request, *args, **kwargs):
        serializer = LocationSerializer(data=request.data)
        lat_str = request.data.get('latitude')
        lon_str = request.data.get('longitude')

        lat_enfant = None
        lon_enfant = None
        if lat_str and lon_str:
            lat_enfant = float(lat_str)
            lon_enfant = float(lon_str)
        adresse = request.data.get('adresse')
        
        enfant_slug = request.data.get('enfant')
        imei = request.data.get('device')

        child = None
        device = None

        # Cas 1 : slug enfant fourni
        if enfant_slug:
            try:
                child = Child.objects.get(slug=enfant_slug)
                request.data['enfant'] = child.pk
            except Child.DoesNotExist:
                return Response({
                    "data": None,
                    "message": "Aucun enfant trouvé avec ce slug",
                    "success": False,
                    "code": 400
                }, status=status.HTTP_400_BAD_REQUEST)

        # Cas 2 : IMEI du device fourni
        elif imei:
            try:
                device = Device.objects.get(imei=imei)
                request.data['device'] = device.pk

                # Si le Device est lié à un enfant
                if device.child:
                    request.data['enfant'] = device.child.pk
                    child = device.child
            except Device.DoesNotExist:
                return Response({
                    "data": None,
                    "message": "Aucun device trouvé avec cet IMEI",
                    "success": False,
                    "code": 400
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                "data": None,
                "message": "Aucun identifiant fourni (ni enfant, ni IMEI)",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.is_valid():
            location = serializer.save()
            if child:
                perimetre_securite = ChildWithPerimetreSecurite.objects.filter(child__slug=enfant_slug,is_active=True).first()
                if perimetre_securite :
                    resultat = verifier_enfant_dans_zone(enfant_slug, lat_enfant, lon_enfant,adresse)
            elif device:
                perimetre_securite = ChildWithPerimetreSecurite.objects.filter(device__slug=device.slug,is_active=True).first()
                if perimetre_securite :
                    resultat = verifier_enfant_dans_zone_device(device.slug, lat_enfant, lon_enfant,adresse)
            return Response({
                "data": {
                    "location": LocationSerializer(location).data
                },
                "message": "Emplacement de l'enfant enregistré avec succès",
                "success": True,
                "code": 200,
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "data": None,
                "message": serializer.errors,
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

# recuperer le dernier emplacement de l'enfant 
class LastPosition(generics.RetrieveAPIView):
    serializer_class = LocationSerializer
    queryset = Child.objects.all()
    lookup_field = 'slug'
    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')

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
            last_emplacement = Location.objects.filter(enfant=child,location_type="gps").last()
        elif device:
            last_emplacement = Location.objects.filter(device=device,location_type="gps").last()
        else:
            return Response({
                "data": None,
                "message": "Enfant ou appareil non trouvé",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

        if last_emplacement:
            serializer = self.get_serializer(last_emplacement)
            return Response({
                "data": serializer.data,
                "message": "Dernier emplacement de l'enfant récupéré avec succès",
                "success": True,
                "code": 200
            })
        else:
            return Response({
                "data": None,
                "message": "Aucun emplacement trouvé pour cet enfant ou device",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)
# Recupere la trajectoir de l'enfant les differente point enregistre dans la journés
class DailyTrajectoryView(generics.ListAPIView):
    serializer_class = LocationSerializer

    def get(self, request, type="24hours", *args, **kwargs):
        slug = self.kwargs.get('slug')
        
        # Vérifier si l'enfant existe   
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

        today = timezone.now()

        if type == "7days":
            start_date = today - timedelta(days=7)
        elif type == "30days":
            start_date = today - timedelta(days=30)
        elif type == "90days":
            start_date = today - timedelta(days=90)
        elif type == "24hours":
            start_date = today - timedelta(days=1)
        else:
            return Response({
                "data": None,
                "message": "Type de période non valide. Utilisez '7days', '30days', ou '90days'.",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        # Filtrer les emplacements de l'enfant pour la période spécifiée
        if child:
            locations = Location.objects.filter(
                enfant=child,location_type="gps",
                datetime_localisation__gte=start_date,
                datetime_localisation__lt=today
            ).order_by('-datetime_localisation')
        elif device:
            locations = Location.objects.filter(
                device=device,location_type="gps",
                datetime_localisation__gte=start_date,
                datetime_localisation__lt=today
            ).order_by('-datetime_localisation')
        else:
            return Response({
                "data": None,
                "message": "Enfant ou appareil non trouvé",
                "success": False,
                "code": 404
            }, status=status.HTTP_404_NOT_FOUND)

        if locations.exists():
            serializer = self.get_serializer(locations, many=True)
            formatted_data = []
            for loc in serializer.data:
                # Convertir datetime_localisation en objet datetime si c'est une chaîne
                datetime_str = loc['datetime_localisation']
                datetime_obj = parse_datetime(datetime_str) if isinstance(datetime_str, str) else datetime_str
                if datetime_obj:
                    nom = None
                    prenom = None
                    if child:
                        nom = child.nom
                        prenom = child.prenom
                    elif device:
                        nom = device.nom
                        prenom = device.prenom
                    formatted_data.append({
                        "data" : loc,
                        "detail_message": f"Vous avez consulté l'historique des déplacements de {prenom}. {nom} s'est rendu(e) à “{loc['adresse']}” le {timezone.localtime(datetime_obj).strftime('%d %B à %Hh%M')}."
                    })
            return Response({
                "data": formatted_data,
                "message": "Trajectoire de l'enfant récupérée avec succès",
                "success": True,
                "code": 200
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "data": None,
                "message": "Aucun emplacement trouvé pour cet enfant sur la période spécifiée",
                "success": True,
                "code": 200
            }, status=status.HTTP_200_OK)


# views pour ajouter les alergy de l'enfant
class ChildAlergyApiViews(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Allergy.objects.all()
    serializer_class = ChildAlergySerializer

    def get(self, request):
        allergies = Allergy.objects.all()
        serializers = ChildAlergySerializer(allergies, many=True)
        return Response({'data': {'child': serializers.data}, 'message': "Child allergy list", 'success': True, 'code': 200}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Assurez-vous que 'child' est un entier
        if 'child' in request.data:
            try:
                request.data['child'] = int(request.data['child'])
            except ValueError:
                return Response({'data': None, 'message': {'child': ['Invalid child ID. Must be an integer.']}, 'success': False, 'code': 400}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ChildAlergySerializer(data=request.data)
        if serializer.is_valid():
            childAllergy = serializer.save()
            return Response({'data': {'allergy': ChildAlergySerializer(childAllergy).data}, 'message': "Child allergy added successfully", 'success': True, 'code': 200}, status=status.HTTP_201_CREATED)
        else:
            return Response({'data': None, 'message': serializer.errors, 'success': False, 'code': 400}, status=status.HTTP_400_BAD_REQUEST)


# Creer un child qui sera valider par la par le parent une foix que les donné serons renseinger

class parentResisterChild(generics.RetrieveAPIView):
    serializers_class = ChildSerializer
    queryset = Child.objects.all()
    def post(self, request, *args, **kwargs):
        child = Child.objects.create(
            date_de_naissance = timezone.now().date(),
            user_type = 'CHILD',
            is_active = False
        )
        return Response({'data': ChildSerializer(child).data, 'message': "Veillez renseignez les information de l'enfant", 'success': True, 'code': 200}, status=status.HTTP_200_OK)

# La nouvelle methode pour valider la creation du compte de lenfant par le parent
class ParentValidateChildDataAndLink(generics.RetrieveAPIView):
    serializer_class = ChildSerializer
    queryset = Child.objects.all()
    lookup_field = 'slug'

    def put(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        slug_parent = request.data.get('slug_parent', '')
        relation = request.data.get('relation', '')

        try:
            child = Child.objects.get(slug=slug)
        except Child.DoesNotExist:
            return Response({
                'data': None, 
                'message': "Aucun enfant trouvé", 
                'success': False, 
                'code': 400
            }, status=status.HTTP_400_BAD_REQUEST)
        print("child is active")
        print(child.is_active)
        if child.is_active:
            return self.handle_new_parent_request(child, slug_parent, relation, slug, request)
        else:
            return self.handle_first_link(child, slug_parent, relation, request)

    def handle_first_link(self, child, slug_parent, relation, request):
        # """Création du compte enfant pour la première fois et lien avec le parent principal."""
        serializer = ChildSerializer(child, data=request.data, partial=True)
        # Vérification utilisateur existant
        phone_number = request.data.get('phone_number')
        email = request.data.get('email')
        required_fields = ['prenom', 'nom', 'date_de_naissance','password']
        for field in required_fields:
            if not request.data.get(field):
                return Response({
                    "data": None,
                    "message": f"Le champ {field} est obligatoire",
                    "success": False,
                    "code": 400
                }, status=status.HTTP_400_BAD_REQUEST)
        existing_user_phone = User.objects.filter(phone_number=phone_number).first()
        if email:
            existing_user_email = User.objects.filter(email=email).first()
            if existing_user_email:
                return Response({
                    "data": None,
                    "message": "Un utilisateur avec cet email existe déjà",
                    "success": False,
                    "code": 400
                }, status=status.HTTP_400_BAD_REQUEST)

        if existing_user_phone:
            return Response({
                "data": None,
                "message": "Un utilisateur avec ce numéro de téléphone existe déjà",
                "success": False,
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            try:
                parent = Parent.objects.get(slug=slug_parent)
            except Parent.DoesNotExist:
                return Response({
                    'data': None, 
                    'message': "Aucun parent trouvé pour la création du compte de l'enfant", 
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)

            # Sauvegarde de l'enfant et mot de passe
            serializer.save()
            child.is_active = True
            password = request.data.get('password', '')
            if password:
                child.password = make_password(password)
            child.save()

            # Lier le parent à l'enfant
            family_member, created = FamilyMember.objects.get_or_create(
                parent=parent,
                child=child,
                relation=relation
            )
            # Ajouter le parent aux contacts d'urgence
            if created and not EmergencyContact.objects.filter(parent=parent).exists():
                EmergencyContact.objects.create(
                    parent=parent,
                    phone_number=parent.phone_number,
                    relationship=relation,
                    name=f"{parent.prenom} {parent.nom}"
                )

            # Ajouter allergies et problèmes médicaux
            allergy_type = request.data.get('allergy_type')
            if allergy_type:
                Allergy.objects.create(allergy_type=allergy_type, child=child)

            issue_type = request.data.get('issue_type')
            if issue_type:
                MedicalIssue.objects.create(issue_type=issue_type, child=child)

            return Response({
                "data": {"child": serializer.data},
                "message": "Enfant inscrit avec succès",
                "success": True,
                "code": 200
            }, status=status.HTTP_200_OK)

        return Response({
            "data": None,
            "message": serializer.errors,
            "success": False,
            "code": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    def handle_new_parent_request(self, child, slug_parent, relation, slug, request):
        """Envoyer une demande de co-parenting au parent principal."""
        exists = FamilyMember.objects.filter(parent__slug=slug_parent, child__slug=slug).exists()
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

        first_family_member = FamilyMember.objects.filter(child=child).order_by('created_at').first()

        comment = f"Un nouveau parent souhaite ajouter {child.prenom} {child.nom}."
        notification = AlertNotification.objects.create(type_notification="demande", parent=parent, comment=comment)
        Demande.objects.create(
            enfant=child,
            parent=parent,
            parent_recepteur=first_family_member.parent,
            relationship=relation,
            notification=notification
        )

        # Message unique pour notification et SMS
        message_text = f"Bonjour {parent.prenom} {parent.nom} a exprimé le souhait de devenir co-parent pour votre enfant {child.prenom} {child.nom}. Votre décision est essentielle pour renforcer le cercle de protection de votre enfant."

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


# Va retourner les autres possible relation que l'enfant peux avoir apres deja ses quelque relation sur familyMember
class ChildParentRelationship(generics.CreateAPIView):
    serializer_class = FamilyMemberSerializer
    queryset = FamilyMember.objects.all()
    
    def get(self, request, slug, *args, **kwargs):
        slug_parent = request.data.get('slug_parent', '')

        try:
            parent = Parent.objects.get(slug=slug_parent)
        except Parent.DoesNotExist:
            return Response({"data": {"data": None,},"message": "Le parent doit dabord avoir un compte","success": True,"code": 200}, status=status.HTTP_200_OK)
        try:
            child = Child.objects.get(slug=slug)
        except Parent.DoesNotExist:
            return Response({ "data": { "data": None},"message": "Aucun enfant trouver pour ce compte","success": True,"code": 200}, status=status.HTTP_200_OK)
        
        # Définir les relations possibles par genre
        male_relationships = [
            {"libelle": "Papa", "image": "/mediafile/avatars/papaProfile.png"},
            {"libelle": "Oncle", "image": "/mediafile/avatars/oncleProfile.png"},
            {"libelle": "Grand-père", "image": "/mediafile/avatars/grand_pereProfile.png"},
        ]
        
        female_relationships = [
            {"libelle": "Maman", "image": "/mediafile/avatars/mamanProfile.png"},
            {"libelle": "Tante", "image": "/mediafile/avatars/tanteProfile.png"},
            {"libelle": "Grand-mère", "image": "/mediafile/avatars/grand_merProfile.png"},
        ]
        
        # Déterminer les relations possibles en fonction du genre du parent
        if parent.gender == "Homme":
            possible_relationships = male_relationships
        elif parent.gender == "Femme":
            possible_relationships = female_relationships
        else:
            possible_relationships = male_relationships + female_relationships

        # Récupérer les relations actuelles de l'enfant
        child_current_relationships = FamilyMember.objects.filter(child__slug=slug).values_list('relation', flat=True)
        
        # Filtrer les relations possibles pour exclure celles déjà attribuées
        available_relationships = [
            rel for rel in possible_relationships 
            if rel["libelle"] not in child_current_relationships
        ]

        # Retourner les relations disponibles
        return Response({
            "data": {
                "relationships": available_relationships
            },
            "message": "Les relations possibles pour l'enfant",
            "success": True,
            "code": 200
        }, status=status.HTTP_200_OK)
    
# Cette views vas juste nous permetre de retourner les parent d'un enfant
class GetAllParentForthiChild(generics.ListAPIView):
    serializer_class = FamilyMemberSerializer() 
    queryset = FamilyMember.objects.all()
    def get(self, request, slug, *args,**kwargs):
        try:
            family_members = FamilyMember.objects.filter(child__slug=slug)  
        except FamilyMember.DoesNotExist:
            return Response({"data" : None, "message" : "Cet enfant n'est lié à aucun parent", "access" : True, "code" : 200}, status=status.HTTP_200_OK)
        if family_members:
            parent = [family_member.parent for family_member in family_members]
            serializer = ParentSerializer(parent, many=True)
            return Response({"data" : serializer.data , "message" : "Liste des parents", "access" : True, "code" : 200}, status=status.HTTP_200_OK)
        else:
            return Response({"data" : None, "message" : "Cet enfant n'est lié à aucun parent", "access" : True, "code" : 200}, status=status.HTTP_200_OK)