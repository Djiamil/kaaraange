
from api.models import *
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer




class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user_id'] = user.id
        data['email'] = user.email
        data['user_type'] = user.user_type
        return data

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # exclude = ['password']
        fields = '__all__'

class ParentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        # exclude = ['password']
        fields = '__all__'

class PendingUserGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingUser
        fields = '__all__'

class OtpGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = '__all__'

class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Child
        fields = '__all__'
        lookup_field = 'slug'

class ParentChildLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentChildLink
        fields = ['id','slug', 'child', 'qr_code']

class MedicalIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalIssue
        fields = ['id', 'issue_type', 'description', 'date_identified', 'treatment_details']

class ChildAlergySerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergy
        fields = ['id', 'child', 'allergy_type', 'description', 'date_identified']


        
class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class ChildSerializerDetail(serializers.ModelSerializer):
    medical_issues = MedicalIssueSerializer(read_only=True,many=True)
    allergies = ChildAlergySerializer(read_only=True, many=True)
    last_location = serializers.SerializerMethodField()
    
    class Meta:
        model = Child
        fields = ['id', 'slug', 'email', 'phone_number', 'password', 'prenom', 'nom', 'is_active', 'is_archive',
                  'user_type', 'accepted_terms', 'registration_method', 'otp_token',
                  'gender', 'date_de_naissance', 'type_appareil', 'numeros_urgences',
                  'ecole','battery_level', 'avatar', 'allergies', 'medical_issues', 'last_location']

    def get_last_location(self, obj):
        # Récupère la dernière localisation pour l'enfant
        last_location = Location.objects.filter(enfant=obj).order_by('-datetime_localisation').first()
        if last_location:
            return LocationSerializer(last_location).data
        return None
        
class RetrieveAPIView(serializers.ModelSerializer):
        
        class Meta:
            model = Parent
            fields = '__all__'



class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = '__all__'

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'parent', 'name', 'phone_number', 'relationship']

class EmergencyAlertSerializer(serializers.ModelSerializer):
    child = ChildSerializerDetail()
    class Meta:
        model =EmergencyAlert
        fields = '__all__'

class AlertNotificationSerializer(serializers.ModelSerializer):
    alert = EmergencyAlertSerializer()
    parent = ParentSerializer()
    
    class Meta:
        model =AlertNotification
        fields = '__all__'


class PointTrajetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointTrajet
        fields = '__all__'

class PerimetreSecuriteSerializer(serializers.ModelSerializer):
    point_trajet = PointTrajetSerializer()
    enfant = ChildSerializer()
    class Meta:
        model = PerimetreSecurite
        fields = '__all__'
        
class PerimetreaddSecuriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerimetreSecurite
        fields = '__all__'

class DemandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demande
        fields = '__all__'

class DetailDemandeSerializer(serializers.ModelSerializer):
    enfant = ChildSerializer()
    parent_emeteur = ParentSerializer(source='parent')
    parent_recepteur = ParentSerializer() 
    notification = AlertNotificationSerializer()
    
    class Meta:
        model = Demande  # Correction ici
        fields = '__all__'

class ChildWithPerimetreSecuriteSerializer(serializers.ModelSerializer):
    child = ChildSerializer()  # Charger les détails de l'enfant
    class Meta:
        model = ChildWithPerimetreSecurite
        fields = '__all__'


class ListeChildWithPerimetreSecuriteSerializer(serializers.ModelSerializer):
    child_slug = serializers.CharField(source="child.slug")
    child_nom = serializers.CharField(source="child.nom")

    class Meta:
        model = ChildWithPerimetreSecurite
        fields = ["child_slug", "child_nom", "is_active"]

class ListePerimetreSecuriteSerializer(serializers.ModelSerializer):
    enfants_associes = serializers.SerializerMethodField()
    

    class Meta:
        model = PerimetreSecurite
        fields = ["slug", "libelle", "rayon", "latitude", "longitude", "enfants_associes"]

    def get_enfants_associes(self, obj):
        enfants = obj.childwithperimetresecurite_set.all()
        return ChildWithPerimetreSecuriteSerializer(enfants, many=True).data if enfants else []

class PerimetreAssocieSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(source="perimetre_securite.slug")
    libelle = serializers.CharField(source="perimetre_securite.libelle")
    rayon = serializers.FloatField(source="perimetre_securite.rayon")
    latitude = serializers.FloatField(source="perimetre_securite.latitude")
    longitude = serializers.FloatField(source="perimetre_securite.longitude")
    is_active = serializers.BooleanField()

    class Meta:
        model = ChildWithPerimetreSecurite
        fields = ["slug", "libelle", "rayon", "latitude", "longitude", "is_active"]

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'
        
class SerializerBatteryStatus(serializers.ModelSerializer):
    class Meta:
        model = BatteryStatus
        fields = '__all__'

class FamilyNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyNumber
        fields = ['id', 'device', 'number', 'serialnumber', 'name', 'url']
        read_only_fields = ['serialnumber', 'name']

    def create(self, validated_data):
        device = validated_data["device"]
        existing_numbers = FamilyNumber.objects.filter(device=device).count()

        if existing_numbers >= 3:
            raise serializers.ValidationError("Ce device a déjà 3 numéros enregistrés.")

        # Attribution automatique du serialnumber
        validated_data["serialnumber"] = existing_numbers

        # Attribution automatique du nom : "111", "222", "333"
        names = ["111", "222", "333"]
        validated_data["name"] = names[existing_numbers]

        return super().create(validated_data)
