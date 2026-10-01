from django.db import models
from apps.core.models import TimeStampedModel


class DeliveryZone(TimeStampedModel):
    country = models.ForeignKey(
        "countries.Country",
        on_delete=models.CASCADE,
        related_name="delivery_zones",
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.name} ({self.country.code})"


class DeliveryMethod(TimeStampedModel):
    store = models.ForeignKey(
        "stores.Store",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="delivery_methods",
    )
    country = models.ForeignKey(
        "countries.Country",
        on_delete=models.CASCADE,
        related_name="delivery_methods",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estimated_days = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.cost}"


class ShipmentStatus(models.TextChoices):
    PREPARING = "PREPARING", "En préparation"
    IN_TRANSIT = "IN_TRANSIT", "En cours de livraison"
    DELIVERED = "DELIVERED", "Livrée"
    FAILED = "FAILED", "Échec de livraison"


class Shipment(TimeStampedModel):
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="shipment",
    )
    delivery_method = models.ForeignKey(
        DeliveryMethod,
        on_delete=models.PROTECT,
        related_name="shipments",
    )
    tracking_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.PREPARING,
    )
    carrier_name = models.CharField(max_length=100, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shipment for Order #{self.order.order_number}"
