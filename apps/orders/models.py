from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    PAID = "PAID", "Payée"
    PROCESSING = "PROCESSING", "En préparation"
    SHIPPED = "SHIPPED", "Expédiée"
    DELIVERED = "DELIVERED", "Livrée"
    CANCELLED = "CANCELLED", "Annulée"
    REFUNDED = "REFUNDED", "Remboursée"


class Order(TimeStampedModel):
    order_number = models.CharField(max_length=64, unique=True, db_index=True)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    campaign = models.ForeignKey(
        "campaigns.Campaign",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    campaign_participant = models.OneToOneField(
        "campaigns.CampaignParticipant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order",
    )
    currency = models.ForeignKey(
        "countries.Currency",
        on_delete=models.PROTECT,
        related_name="orders",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    shipping_address = models.TextField()
    contact_phone = models.CharField(max_length=30)

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.order_number} ({self.get_status_display()})"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} ({self.order.order_number})"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
