from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE_CASCADE
from django.contrib.auth.models import BaseUserManager 
import uuid 


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
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


# la model user que vons heriter tous les autre model de type user comme parent child et tuteur ...
class User(AbstractBaseUser, PermissionsMixin, SafeDeleteModel):
    slug = models.SlugField(default=uuid.uuid1)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_archive = models.BooleanField(default=False)
    user_type = models.CharField(max_length=50, choices=USER_TYPES, default='PARENT')
    accepted_terms = models.BooleanField(default=False, verbose_name="Accepté les conditions d'utilisation")
    registration_method = models.CharField(max_length=50, choices=REGISTRATION_METHOD, default='normal')
    otp_token = models.CharField(max_length=6, null=True, blank=True, verbose_name="Token OTP")
    gender = models.CharField(max_length=10, null=True, blank=True, verbose_name="Genre")
    objects = CustomUserManager()

    _safedelete_policy = SOFT_DELETE_CASCADE
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def get_by_natural_key(self, email):
        return self.get(email=email)

# Le model parent qui represente les utilisateur de type parent
class Parent(User):
    adresse = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=20, null=True)



# le model child qui herite aussi du models user est reprensente les utilisteur de type enfant
class Child(User):
    date_de_naissance = models.DateField()
    type_appareil = models.CharField(max_length=100)
    numeros_urgences = models.TextField()
    ecole = models.CharField(max_length=100, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)

# le model ParentChildLink nous permetrat maintenant juste de relier un enfant a un qrcode
class ParentChildLink(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    # parent = models.ForeignKey(Parent, on_delete=models.CASCADE, blank=True, null=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    qr_code = models.TextField(blank=True, null=True)  # Modifier le champ qr_code


    def __str__(self):
        return f"{self.parent} - {self.child}"


class FamilyMember(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    relation = models.CharField(max_length=100, choices=RELATIONSHIP_CHOICES)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, blank=True, null=True)
    child = models.ForeignKey(Child, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.relation}: {self.parent} - {self.child}"


# Model de creation temporel des utilisateur en attendant la validation de l'otp 
class PendingUser(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    email = models.EmailField(unique=True, default="")
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
    date_de_naissance = models.DateField(null=True, blank=True)
    is_archive = models.BooleanField(default=False, verbose_name="Accepté les conditions d'utilisation")

    class Meta:
        verbose_name_plural = "Utilisateurs en attente"


    def __str__(self):
        return self.prenom

# Le model pour enregistre les code otp qui serons envoyer comme verification du numero lors de l'inscription du parent
class OTP(models.Model):
    slug = models.SlugField(default=uuid.uuid1)
    pending_user = models.OneToOneField(PendingUser,null=True, blank=True, on_delete=models.CASCADE, default=None)
    otp_code = models.CharField(max_length=6)

    def __str__(self):
        return f"OTP pour {self.user.username}"
    
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

# super admin kaaraange@gmail.com gthub prof edacy Darcia0001@gmail.com
