from django.db import models
from apps.core.models import TimeStampedModel


class Store(TimeStampedModel):
    merchant = models.ForeignKey(
        "merchants.MerchantProfile",
        on_delete=models.CASCADE,
        related_name="stores",
    )
    country = models.ForeignKey(
        "countries.Country",
        on_delete=models.PROTECT,
        related_name="stores",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="stores/logos/", null=True, blank=True)
    banner = models.ImageField(upload_to="stores/banners/", null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Boutique"
        verbose_name_plural = "Boutiques"

    def __str__(self):
        return f"{self.name} ({self.country.code})"
