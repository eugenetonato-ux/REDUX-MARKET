from django.contrib import admin
from .models import DeliveryZone, DeliveryMethod, Shipment


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "code")


@admin.register(DeliveryMethod)
class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "cost", "estimated_days", "is_active")
    list_filter = ("is_active", "country")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("order", "delivery_method", "status", "tracking_number", "shipped_at", "delivered_at")
    list_filter = ("status",)
