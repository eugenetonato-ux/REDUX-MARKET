from django.contrib import admin
from .models import PriceTier


@admin.register(PriceTier)
class PriceTierAdmin(admin.ModelAdmin):
    list_display = ("campaign", "min_participants", "max_participants", "price", "discount_percentage")
    list_filter = ("campaign",)
