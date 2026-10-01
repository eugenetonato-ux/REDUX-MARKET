from django.contrib import admin
from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "merchant", "country", "city", "is_active", "rating_average")
    list_filter = ("is_active", "country")
    search_fields = ("name", "merchant__business_name", "city")
    prepopulated_fields = {"slug": ("name",)}
