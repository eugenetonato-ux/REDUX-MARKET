from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class DisputeStatus(models.TextChoices):
    OPEN = "OPEN", "Ouvert"
    UNDER_REVIEW = "UNDER_REVIEW", "En cours d'examen"
    RESOLVED = "RESOLVED", "Résolu"
    CLOSED = "CLOSED", "Fermé"


class Dispute(TimeStampedModel):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="disputes",
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="disputes",
    )
    reason = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=DisputeStatus.choices,
        default=DisputeStatus.OPEN,
        db_index=True,
    )
    resolution = models.TextField(blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Litige #{self.pk} - Order {self.order.order_number}"


class DisputeMessage(TimeStampedModel):
    dispute = models.ForeignKey(
        Dispute,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    message = models.TextField()
    attachment = models.FileField(upload_to="disputes/attachments/", null=True, blank=True)

    def __str__(self):
        return f"Message by {self.sender} on Dispute #{self.dispute_id}"
