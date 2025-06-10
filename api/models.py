from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE_CASCADE
from django.contrib.auth.models import BaseUserManager 
import uuid 
from django.utils import timezone

from firebase_admin import messaging
from api.firebase_setup import initialize_firebase

# Initialiser Firebase
initialize_firebase()



ADMIN = 'admin'
PARENT = 'parent'
CHILD = 'child'
TUTEUR = 'tuuteur'
USER_TYPES = (
    ('ADMIN', 'ADMIN'),
    ('PARENT', 'PARENT'),
    ('CHILD', 'CHILD'),
    ('TUTEUR', 'TUTEUR'),
)

GOOGLE  = 'google'
FACEBOOK = 'facebook'
APPLE = 'apple'
NORMAL = 'normal'
REGISTRATION_METHOD = (
    ('GOOGLE', 'GOOGLE'),
    ('FACEBOOK', 'FACEBOOK'),
    ('APPLE', 'APPLE'),
    ('NORMAL', 'NORMAL'),
)

# PAPA = 'papa'
# MAMAN = 'maman'
# TANTE = 'tante'
# ONCLE = 'oncle'
# GRAND_MERE = 'grand-mere'
# GRAND_PERE = 'grand-pere'
# RELATIONSHIP_CHOICES = [
#     (PAPA, 'Papa'),
#     (MAMAN, 'Maman'),
#     (TANTE, 'Tante'),
#     (ONCLE, 'Oncle'),
#     (GRAND_MERE, 'Grand-mère'),
#     (GRAND_PERE, 'Grand-père'),
# ]


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)  # Définition de is_staff sur True
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


# la model user que vons heriter tous les autre model de type user comme parent child et tuteur ...
class User(AbstractBaseUser, PermissionsMixin, SafeDeleteModel):
    slug = models.SlugField(default=uuid.uuid1)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255)
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_archive = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    user_type = models.CharField(max_length=50, choices=USER_TYPES, default='PARENT')
    accepted_terms = models.BooleanField(default=False, verbose_name="Accepté les conditions d'utilisation")
    registration_method = models.CharField(max_length=50, choices=REGISTRATION_METHOD, default='normal')
    otp_token = models.CharField(max_length=6, null=True, blank=True, verbose_name="Token OTP")
    gender = models.CharField(max_length=10, null=True, blank=True, verbose_name="Genre")
    objects = CustomUserManager()
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Avatar")
    fcm_token = models.CharField(max_length=255, null=True, blank=True, verbose_name="FCM Token")  # Ajout du FCM Token



    _safedelete_policy = SOFT_DELETE_CASCADE
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']
 
    def __str__(self):
        return self.email or "No Email"

    def get_by_natural_key(self, email):
        return self.get(email=email)

# Le model parent qui represente les utilisateur de type parent
class Parent(User):
    adresse = models.CharField(max_length=255, blank=True, null=True)


# le model child qui herite aussi du models user est reprensente les utilisteur de type enfant
class Child(User):
    date_de_naissance = models.DateField()
    type_appareil = models.CharField(max_length=100)
    vous_appelle_til = models.CharField(max_length=100, blank=True, null=True)
    numeros_urgences = models.TextField()
    ecole = models.CharField(max_length=100, blank=True, null=True)
    battery_level = models.IntegerField(default=100, help_text="Niveau de batterie en pourcentage (0-100)")


# le model ParentChildLink nous permetrat maintenant juste de relier un enfant a un qrcode
class ParentChildLink(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    # parent = models.ForeignKey(Parent, on_delete=models.CASCADE, blank=True, null=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    qr_code = models.TextField(blank=True, null=True)  # Modifier le champ qr_code
    created_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.child} - {self.child}"

class FamilyMember(models.Model):
    PAPA = 'papa'
    MAMAN = 'maman'
    TANTE = 'tante'
    ONCLE = 'oncle'
    GRAND_MERE = 'grand-mere'
    GRAND_PERE = 'grand-pere'

    RELATIONSHIP_CHOICES = [
        (PAPA, 'Papa'),
        (MAMAN, 'Maman'),
        (TANTE, 'Tante'),
        (ONCLE, 'Oncle'),
        (GRAND_MERE, 'Grand-mère'),
        (GRAND_PERE, 'Grand-père'),
    ]
    slug = models.SlugField(default=uuid.uuid1)
    relation = models.CharField(max_length=100, choices=RELATIONSHIP_CHOICES)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, blank=True, null=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, null=True,blank=True)  # Ajout de created_at

    def __str__(self):
        return f"{self.relation}: {self.parent} - {self.child}"


# Model de creation temporel des utilisateur en attendant la validation de l'otp 
class PendingUser(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    email = models.EmailField(unique=False, null=True,blank=True)
    password = models.CharField(max_length=255)
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    user_type = models.CharField(max_length=50, choices=USER_TYPES, default='PARENT')
    accepted_terms = models.BooleanField(default=False, verbose_name="Accepté les conditions d'utilisation")
    registration_method = models.CharField(max_length=50, choices=REGISTRATION_METHOD, default='normal')
    otp_token = models.CharField(max_length=6, null=True, blank=True, verbose_name="Token OTP")
    gender = models.CharField(max_length=10, null=True, blank=True, verbose_name="Genre")
    telephone = models.CharField(max_length=15, null=True, blank=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    is_archive = models.BooleanField(default=False, verbose_name="Accepté les conditions d'utilisation")
    date_de_naissance = models.DateField(blank=True, null=True)
    type_appareil = models.CharField(max_length=100,blank=True, null=True)
    numeros_urgences = models.TextField(blank=True, null=True)
    ecole = models.CharField(max_length=100, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Avatar")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Utilisateurs en attente"


    def __str__(self):
        return self.prenom

# Le model pour enregistre les code otp qui serons envoyer comme verification du numero lors de l'inscription du parent
class OTP(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    pending_user = models.OneToOneField(PendingUser,null=True, blank=True, on_delete=models.CASCADE, default=None)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        if self.pending_user:
            return f"OTP pour {self.pending_user.email}"
        else:
            return "OTP sans utilisateur associé"

# Model pour stocker tous les sms envoyer
class SMS(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    accountid = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    sender = models.CharField(max_length=11)
    ret_id = models.CharField(max_length=255, blank=True, null=True)
    ret_url = models.URLField(blank=True, null=True)
    start_date = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.CharField(max_length=255, blank=True, null=True)
    stop_time = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField()
    to = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)


# Model pour jouter non divices
class Device(models.Model):
    imei = models.CharField(max_length=20, unique=True)
    model_name = models.CharField(max_length=50)
    dev_type = models.CharField(max_length=20)
    child = models.OneToOneField(Child, on_delete=models.CASCADE, related_name="device", null=True, blank=True)

    def __str__(self):
        return f"{self.model_name} ({self.imei})"
    
# Model pour stoquer les position de l'enfant
class Location(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    enfant = models.ForeignKey(Child, on_delete=models.SET_NULL, null=True, blank=True)  # nullable
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name="locations")  # nullable
    latitude = models.CharField(max_length=50, null=True, blank=True)  # ou une longueur appropriée pour les coordonnées
    longitude = models.CharField(max_length=50, null=True, blank=True)  # ou une longueur appropriée pour les coordonnées
    adresse = models.CharField(max_length=255,null=True, blank=True)
    datetime_localisation = models.DateTimeField(default=timezone.now)
    location_type = models.CharField(
        max_length=10,
        choices=[('gps', 'GPS'), ('wifi', 'Wi-Fi'), ('cell', 'Cell')],
        default='gps'
    )
    wifi_info = models.TextField(blank=True, null=True)
    cell_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.enfant.nom} - {self.adresse} ({self.latitude}, {self.longitude})"

# Model pour enregistre les alergie des enfants
class Allergy(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    id = models.AutoField(primary_key=True)
    child = models.ForeignKey(Child, related_name='allergies', on_delete=models.CASCADE)
    allergy_type = models.CharField(max_length=100)  # Champ de texte libre pour le type d'allergie
    description = models.TextField(blank=True, null=True)
    date_identified = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.allergy_type} allergy for {self.child.nom}"
    
# Model pour stocker les probleme medicaux de l'enfant
class MedicalIssue(models.Model):
    slug = models.SlugField(default=uuid.uuid1, unique=True)
    id = models.AutoField(primary_key=True)
    child = models.ForeignKey(Child, related_name='medical_issues', on_delete=models.CASCADE)
    issue_type = models.CharField(max_length=100)  # Type de problème médical
    description = models.TextField(blank=True, null=True)
    date_identified = models.DateField(default=timezone.now)
    treatment_details = models.TextField(blank=True, null=True)  # Détails sur le traitement

    def __str__(self):
        return f"{self.issue_type} issue for {self.child.nom}"

# Model pour stocker les numero d'urgence a contacter pour les alerte des enfant
class EmergencyContact(models.Model):
    RELATIONSHIP_CHOICES = [
        ('papa', 'Papa'),
        ('maman', 'Maman'),
        ('tuteur', 'Tuteur'),
        ('autre', 'Autre')
    ]
    slug = models.SlugField(default=uuid.uuid1)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.phone_number}"

# model pour enregistrer les alert des enfant vers les numero enregistre par leur parent
class EmergencyAlert(models.Model):
    ALERT_TYPE_CHOICES = [
        ('assistance', 'Assistance'),
        ('danger', 'Danger'),
        ('prevenu', "Prévenu par l'enfant"),
    ]
    ALERT_STATE_CHOICES = [
        ('en_attente', 'En attente'),
        ('traite', 'Traité'),
    ]
    slug = models.SlugField(default=uuid.uuid1)
    id = models.AutoField(primary_key=True)
    child = models.ForeignKey('Child', on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES, default="Prévenu par l'enfant")
    comment = models.TextField()
    alert_datetime = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=20, choices=ALERT_STATE_CHOICES, default='en_attente')
    latitude = models.CharField(max_length=50, blank=True, null=True)  # ou une longueur appropriée pour les coordonnées
    longitude = models.CharField(max_length=50, blank=True, null=True)  # ou une longueur appropriée pour les coordonnées
    adresse = models.CharField(max_length=255, blank=True, null=True)
    datetime_localisation = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"Alert {self.alert_type} for {self.child.nom} on {self.alert_datetime}"

    
class AlertNotification(models.Model):
    NOTIFICATION_TYPE = [
    ('DEMANDE', 'demande'),
    ('alerte', 'alerte'),
    ]
    STATUS_CHOICES = [
        ('en_cours', 'En cours'),
        ('refusé', 'Refusé'),
        ('accepté', 'Accepté'),
    ]
    slug = models.SlugField(default=uuid.uuid1)
    alert = models.ForeignKey(EmergencyAlert, on_delete=models.CASCADE,blank=True, null=True, related_name='notifications')
    contact = models.ForeignKey(EmergencyContact, on_delete=models.CASCADE, blank=True, null=True, related_name='notifications_contact')
    notified_at = models.DateTimeField(auto_now_add=True)
    type_notification = models.CharField(max_length=10, choices=NOTIFICATION_TYPE, default='alerte')
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE,null=True, blank=True, related_name='notification_parents')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='en_cours')  # Nouveau champ
    comment = models.TextField(max_length=10,blank=True,null=True)


    def __str__(self):
        contact_name = self.contact.name if self.contact else "Unknown contact"
        return f"Notification for {contact_name} at {self.notified_at}"
    
    
class EmergencyNumber(models.Model):
    EMERGENCY_TYPE_CHOICES = [
        ('secours', 'Secours'),
        ('autre', 'Autre'),
    ]
    
    slug = models.SlugField(default=uuid.uuid1)
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=10, choices=EMERGENCY_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.get_type_display()} - {self.phone_number}"


# Le model permettant de stocker les point de référence de l'enfant pour la périmetre de securité(Qui n'est plus utiliser par fusion avec le model perimetre de securité)
class PointTrajet(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE,blank=True, null=True)
    enfant = models.ForeignKey(Child, on_delete=models.CASCADE,blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    ordre = models.IntegerField(blank=True, null=True)
    libelle = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Point {self.ordre} - {self.libelle} ({self.latitude}, {self.longitude}) pour {self.parent}"
    
# Models pour stocker l'espace de deplacement de l'enfant en rayon
class PerimetreSecurite(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE,blank=True, null=True)
    rayon = models.FloatField()
    is_active = models.BooleanField(default=False)
    libelle = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Périmètre de sécurité '{self.libelle}' ({self.latitude}, {self.longitude}) - {self.rayon}m"


# Nouvelle process de lier un perimetre de securite a un enfant pour pouvoir l'activer ou la desactiver
class ChildWithPerimetreSecurite(models.Model):
    slug = models.SlugField(default=uuid.uuid4, unique=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    perimetre_securite = models.ForeignKey(PerimetreSecurite, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        
        return f"{self.child.nom} - {self.perimetre_securite.libelle} ({'Actif' if self.is_active else 'Inactif'})"
    
class Demande(models.Model):
    STATUS_CHOICES = [
        ('en_cours', 'En cours'),
        ('refusé', 'Refusé'),
        ('accepté', 'Accepté'),
    ]
    slug = models.SlugField(default=uuid.uuid1)
    enfant = models.ForeignKey(Child, on_delete=models.CASCADE, blank=True, null=True, related_name="demandes")
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, blank=True, null=True, related_name="demandes_envoyees")
    parent_recepteur = models.ForeignKey(Parent, on_delete=models.CASCADE, blank=True, null=True, related_name="demandes_recues")
    relationship = models.CharField(max_length=100)
    notification = models.ForeignKey(AlertNotification, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='en_cours')  # Nouveau champ

    def __str__(self):
        return f"Demande de {self.relationship} pour {self.enfant} au parent {self.parent}"
    
# Model pour stoquer la baterie du divice
class BatteryStatus(models.Model):
    STATUS_CHOICES = [
        ('1', 'Unknown'),
        ('2', 'Charging'),
        ('3', 'Not Charging'),
        ('4', 'Disconnected'),
        ('5', 'Fully Charged'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="battery_statuses")
    battery = models.IntegerField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device} - {self.battery}% ({self.get_status_display()})"




# Ce modèle permettra de stocker les 3 numéros abrégés pour chaque appareil :
class FamilyNumber(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='family_numbers')
    serialnumber = models.IntegerField()  # 0, 1, 2
    number = models.CharField(max_length=20)
    name = models.CharField(max_length=10, null=True, blank=True)
    url = models.URLField(blank=True, null=True)

    class Meta:
        unique_together = ('device', 'serialnumber')  # un seul numéro par bouton par appareil

    def __str__(self):
        return f"{self.device.imei} - {self.name} ({self.serialnumber})"
    
# super admin kaaraange@gmail.com gthub prof edacy Darcia0001@gmail.com

