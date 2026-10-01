from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class RequestStatus(models.TextChoices):
    OPEN = "OPEN", "Ouverte"
    PROPOSALS_RECEIVED = "PROPOSALS_RECEIVED", "Propositions reçues"
    ACCEPTED = "ACCEPTED", "Acceptée"
    EXPIRED = "EXPIRED", "Expirée"
    CANCELLED = "CANCELLED", "Annulée"


class PurchaseRequest(TimeStampedModel):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchase_requests",
    )
    country = models.ForeignKey(
        "countries.Country",
        on_delete=models.PROTECT,
        related_name="purchase_requests",
    )
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_requests",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    target_quantity = models.PositiveIntegerField()
    target_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=30,
        choices=RequestStatus.choices,
        default=RequestStatus.OPEN,
        db_index=True,
    )
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class PurchaseRequestParticipant(TimeStampedModel):
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="purchase_request_pledges",
    )
    quantity_pledged = models.PositiveIntegerField(default=1)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["purchase_request", "user"],
                name="unique_user_purchase_request_pledge",
            )
        ]


class ProposalStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    ACCEPTED = "ACCEPTED", "Acceptée"
    REJECTED = "REJECTED", "Rejetée"
    EXPIRED = "EXPIRED", "Expirée"


class SellerProposal(TimeStampedModel):
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    merchant = models.ForeignKey(
        "merchants.MerchantProfile",
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        related_name="proposals",
    )
    proposed_price = models.DecimalField(max_digits=12, decimal_places=2)
    min_quantity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ProposalStatus.choices,
        default=ProposalStatus.PENDING,
    )
    valid_until = models.DateTimeField()

    def __str__(self):
        return f"Proposal by {self.merchant.business_name} for {self.purchase_request.title}"
