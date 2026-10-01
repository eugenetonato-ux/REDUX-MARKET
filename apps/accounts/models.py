from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from .managers import UserManager
from .roles import UserRole


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True, null=True, blank=True, db_index=True)
    phone = models.CharField(max_length=30, unique=True, null=True, blank=True, db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.BUYER,
        db_index=True,
    )
    country = models.ForeignKey(
        "countries.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email or self.phone or f"User-{self.pk}"

    @property
    def is_buyer(self):
        return self.role == UserRole.BUYER

    @property
    def is_merchant(self):
        return self.role == UserRole.MERCHANT

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser


class BuyerProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="buyer_profile",
    )
    avatar = models.ImageField(upload_to="profiles/avatars/", null=True, blank=True)
    default_shipping_address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    delivery_notes = models.TextField(blank=True)

    def __str__(self):
        return f"BuyerProfile: {self.user}"
