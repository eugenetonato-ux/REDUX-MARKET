from django.db import models
from apps.core.models import TimeStampedModel


class CommissionRule(TimeStampedModel):
    country = models.ForeignKey(
        "countries.Country",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="commission_rules",
    )
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="commission_rules",
    )
    rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    fixed_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Commission {self.rate_percentage}% + {self.fixed_fee}"


class PlatformTransaction(TimeStampedModel):
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="platform_transactions",
    )
    commission_rule = models.ForeignKey(
        CommissionRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2)
    net_merchant_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default="COMPLETED")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commission {self.commission_amount} on Order #{self.order.order_number}"
