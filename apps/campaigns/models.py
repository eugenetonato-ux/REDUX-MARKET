from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class CampaignStatus(models.TextChoices):
    DRAFT = "DRAFT", "Brouillon"
    PENDING_APPROVAL = "PENDING_APPROVAL", "En attente d'approbation"
    ACTIVE = "ACTIVE", "Active"
    TARGET_REACHED = "TARGET_REACHED", "Objectif atteint"
    PAYMENT_PENDING = "PAYMENT_PENDING", "Paiements en attente"
    SUCCESS = "SUCCESS", "Succès"
    FAILED = "FAILED", "Échouée"
    EXPIRED = "EXPIRED", "Expirée"
    CANCELLED = "CANCELLED", "Annulée"
    SUSPENDED = "SUSPENDED", "Suspendue"


class PricingPolicy(models.TextChoices):
    CURRENT_TIER_PRICE = "CURRENT_TIER_PRICE", "Prix du palier au moment de l'adhésion"
    FINAL_TIER_PRICE = "FINAL_TIER_PRICE", "Prix du palier final atteint"


class Campaign(TimeStampedModel):
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    merchant = models.ForeignKey(
        "merchants.MerchantProfile",
        on_delete=models.CASCADE,
        related_name="campaigns",
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_campaigns",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    status = models.CharField(
        max_length=30,
        choices=CampaignStatus.choices,
        default=CampaignStatus.DRAFT,
        db_index=True,
    )
    pricing_policy = models.CharField(
        max_length=30,
        choices=PricingPolicy.choices,
        default=PricingPolicy.CURRENT_TIER_PRICE,
    )
    target_participants = models.PositiveIntegerField(default=10)
    min_participants = models.PositiveIntegerField(default=2)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    current_participants_count = models.PositiveIntegerField(default=0)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(db_index=True)
    terms = models.TextField(blank=True)

    class Meta:
        verbose_name = "Campagne"
        verbose_name_plural = "Campagnes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class CampaignParticipantStatus(models.TextChoices):
    JOINED = "JOINED", "Inscrit"
    CONFIRMED = "CONFIRMED", "Confirmé"
    CANCELLED = "CANCELLED", "Annulé"
    REFUNDED = "REFUNDED", "Remboursé"


class CampaignParticipant(TimeStampedModel):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="campaign_participations",
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=CampaignParticipantStatus.choices,
        default=CampaignParticipantStatus.JOINED,
        db_index=True,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "user"],
                condition=models.Q(status="JOINED"),
                name="unique_active_user_participation",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.campaign.title} (x{self.quantity})"


class CampaignView(models.Model):
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="views",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    viewed_at = models.DateTimeField(auto_now_add=True)
