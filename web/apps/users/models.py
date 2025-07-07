from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from apps.common.models import TimeStampedModel # Assurez-vous que ce chemin est correct

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'utilisateur doit avoir une adresse email')
        if not username:
            raise ValueError('L\'utilisateur doit avoir un nom d\'utilisateur')

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Superuser should be active by default

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le Superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le Superuser doit avoir is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True, verbose_name="Adresse Email")
    username = models.CharField(max_length=150, unique=True, verbose_name="Nom d'utilisateur")
    first_name = models.CharField(max_length=150, blank=True, verbose_name="Prénom")
    last_name = models.CharField(max_length=150, blank=True, verbose_name="Nom de famille")

    is_staff = models.BooleanField(default=False, verbose_name="Membre du personnel")
    is_active = models.BooleanField(default=True, verbose_name="Actif") # Active by default, can be deactivated
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Date d'inscription")

    # TimeStampedModel fournit déjà: id (UUID), created_at, updated_at

    objects = UserManager()

    USERNAME_FIELD = 'email' # Utiliser l'email pour se connecter
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name'] # Champs demandés lors de la création d'un superutilisateur

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['email']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name


class Company(TimeStampedModel):
    name = models.CharField(max_length=255, verbose_name="Nom de la société")
    address = models.TextField(null=True, blank=True, verbose_name="Adresse")
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True, verbose_name="Logo")
    owner = models.ForeignKey(
        User,
        related_name='owned_companies',
        on_delete=models.CASCADE, # Si l'utilisateur est supprimé, ses sociétés le sont aussi
        verbose_name="Propriétaire"
    )
    # is_active_for_owner = models.BooleanField(default=True) # Peut être géré autrement (ex: UserProfile ou session)

    # Autres champs potentiels : siret, vat_number, phone, email_contact, website.

    class Meta:
        verbose_name = "Société"
        verbose_name_plural = "Sociétés"
        ordering = ['name']
        # Unique constraint for company name per owner, if desired
        # unique_together = ('owner', 'name')


    def __str__(self):
        return self.name
