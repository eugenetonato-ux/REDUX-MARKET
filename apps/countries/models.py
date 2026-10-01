from django.db import models
from apps.core.models import TimeStampedModel


class Currency(TimeStampedModel):
    code = models.CharField(max_length=3, unique=True)  # XOF, USD, EUR
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)            # CFA, $, €
    decimals = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Currencies"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.symbol})"


class Country(TimeStampedModel):
    code = models.CharField(max_length=2, unique=True)  # BJ, CI, SN, etc.
    name = models.CharField(max_length=100)
    phone_prefix = models.CharField(max_length=10)      # +229
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="countries")
    is_active = models.BooleanField(default=True)
    flag_emoji = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"
