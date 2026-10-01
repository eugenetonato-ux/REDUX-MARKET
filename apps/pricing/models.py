from django.db import models
from apps.core.models import TimeStampedModel


class PriceTier(TimeStampedModel):
    campaign = models.ForeignKey(
        "campaigns.Campaign",
        on_delete=models.CASCADE,
        related_name="tiers",
    )
    min_participants = models.PositiveIntegerField()
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["min_participants"]
        verbose_name = "Palier de prix"
        verbose_name_plural = "Paliers de prix"

    def __str__(self):
        max_str = self.max_participants if self.max_participants else "+"
        return f"{self.min_participants}-{max_str} participants: {self.price}"
