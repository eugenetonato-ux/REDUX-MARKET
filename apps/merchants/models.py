from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    VERIFIED = "VERIFIED", "Vérifié"
    REJECTED = "REJECTED", "Rejeté"
    SUSPENDED = "SUSPENDED", "Suspendu"


class MerchantProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="merchant_profile",
    )
    business_name = models.CharField(max_length=200)
    business_type = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Profil Commerçant"
        verbose_name_plural = "Profils Commerçants"

    def __str__(self):
        return f"{self.business_name} ({self.get_verification_status_display()})"

    @property
    def is_verified(self):
        return self.verification_status == VerificationStatus.VERIFIED


class MerchantVerification(TimeStampedModel):
    merchant = models.ForeignKey(
        MerchantProfile,
        on_delete=models.CASCADE,
        related_name="verifications",
    )
    document_type = models.CharField(max_length=100)
    document_file = models.FileField(upload_to="merchant_documents/")
    status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Document {self.document_type} - {self.merchant}"
