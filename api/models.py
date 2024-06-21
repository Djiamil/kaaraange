from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE_CASCADE
from django.contrib.auth.models import BaseUserManager 
import uuid 
from django.utils import timezone



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


    _safedelete_policy = SOFT_DELETE_CASCADE
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']
 
    def __str__(self):
        return self.email

    def get_by_natural_key(self, email):
        return self.get(email=email)

# Le model parent qui represente les utilisateur de type parent
class Parent(User):
    adresse = models.CharField(max_length=255, blank=True, null=True)


# le model child qui herite aussi du models user est reprensente les utilisteur de type enfant
class Child(User):
    date_de_naissance = models.DateField()
    type_appareil = models.CharField(max_length=100)
    numeros_urgences = models.TextField()
    ecole = models.CharField(max_length=100, blank=True, null=True)

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



class Location(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    enfant = models.ForeignKey(Child, on_delete=models.CASCADE)  # Relation Many-to-One avec Child
    latitude = models.CharField(max_length=50)  # ou une longueur appropriée pour les coordonnées
    longitude = models.CharField(max_length=50)  # ou une longueur appropriée pour les coordonnées
    adresse = models.CharField(max_length=255)
    datetime_localisation = models.DateTimeField(default=timezone.now)

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
    phone_number = models.CharField(max_length=15, unique=True)
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


    def __str__(self):
        return f"Alert {self.alert_type} for {self.child.nom} on {self.alert_datetime}"

    
class AlertNotification(models.Model):
    alert = models.ForeignKey(EmergencyAlert, on_delete=models.CASCADE, related_name='notifications')
    contact = models.ForeignKey(EmergencyContact, on_delete=models.CASCADE)
    notified_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.contact.name} at {self.notified_at}"
    
    
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

# super admin kaaraange@gmail.com gthub prof edacy Darcia0001@gmail.com
