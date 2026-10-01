from django.contrib import admin
from .models import Country, Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "symbol", "decimals", "is_active")
    search_fields = ("code", "name")
    list_filter = ("is_active",)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "phone_prefix", "currency", "is_active")
    search_fields = ("name", "code", "phone_prefix")
    list_filter = ("is_active", "currency")
