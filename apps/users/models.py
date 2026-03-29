from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db import models
from core.models import TimeStampedModel


# ─────────────────────────────────────────────────────
#  Manager
# ─────────────────────────────────────────────────────
class UserManager(BaseUserManager):

    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError('L\'adresse email est obligatoire.')
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)


# ─────────────────────────────────────────────────────
#  Model
# ─────────────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):

    class Role(models.TextChoices):
        ADMIN      = 'admin',      'Administrateur'
        COMMERCANT = 'commercant', 'Commerçant'

    # Champs
    email      = models.EmailField(unique=True, db_index=True)
    nom        = models.CharField(max_length=100)
    telephone  = models.CharField(max_length=20, blank=True)
    adresse    = models.TextField(blank=True)
    role       = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.COMMERCANT,
        db_index=True,
    )
    is_verified = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nom']

    objects = UserManager()

    class Meta:
        db_table     = 'users'
        verbose_name = 'Utilisateur'

    def __str__(self) -> str:
        return f'{self.nom} <{self.email}> [{self.role}]'

    # ── Properties ──────────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_commercant(self) -> bool:
        return self.role == self.Role.COMMERCANT
