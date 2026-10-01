from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    PROCESSING = "PROCESSING", "En cours de traitement"
    SUCCESS = "SUCCESS", "Réussi"
    FAILED = "FAILED", "Échoué"
    CANCELLED = "CANCELLED", "Annulé"


class PaymentProvider(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    countries = models.ManyToManyField("countries.Country", related_name="payment_providers", blank=True)
    supported_currencies = models.ManyToManyField("countries.Currency", related_name="payment_providers", blank=True)

    def __str__(self):
        return self.name


class Payment(TimeStampedModel):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.ForeignKey(
        "countries.Currency",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    reference = models.CharField(max_length=120, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Payment {self.idempotency_key} - {self.amount} {self.currency.code} ({self.get_status_display()})"


class PaymentTransaction(TimeStampedModel):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(max_length=20, default="PAYMENT")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    provider_reference = models.CharField(max_length=120, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    def __str__(self):
        return f"{self.transaction_type} #{self.pk} for Payment {self.payment_id}"


class WebhookEvent(TimeStampedModel):
    provider = models.ForeignKey(
        PaymentProvider,
        on_delete=models.CASCADE,
        related_name="webhook_events",
    )
    event_id = models.CharField(max_length=120, unique=True, db_index=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True)

    def __str__(self):
        return f"Webhook {self.event_id} ({self.provider.code})"


class Refund(TimeStampedModel):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="refunds",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="PENDING")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Refund {self.amount} for Order {self.order.order_number}"
