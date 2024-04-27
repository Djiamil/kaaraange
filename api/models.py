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




class User(AbstractBaseUser, PermissionsMixin, SafeDeleteModel):
    slug = models.SlugField(default=uuid.uuid1)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=1000, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_archive = models.BooleanField(default=False)

    password_reset_count = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True, default=0)
    user_type = models.CharField(max_length=50, choices=USER_TYPES, default='PARENT')
    accepted_terms = models.BooleanField(default=False, verbose_name="Accepté les conditions d'utilisation")
    registration_method = models.CharField(max_length=50, choices=REGISTRATION_METHOD, default='normal')
    otp_token = models.CharField(max_length=6, null=True, blank=True, verbose_name="Token OTP")
    gender = models.CharField(max_length=10, null=True, blank=True, verbose_name="Genre")

    # Utilisez le gestionnaire personnalisé
    objects = CustomUserManager()

    _safedelete_policy = SOFT_DELETE_CASCADE
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    # Implémentez la méthode get_by_natural_key pour le manager personnalisé
    def get_by_natural_key(self, email):
        return self.get(email=email)
    




# super admin kaaraange@gmail.com