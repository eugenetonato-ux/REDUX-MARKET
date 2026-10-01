from django.contrib import admin
from .models import CommissionRule, PlatformTransaction


@admin.register(CommissionRule)
class CommissionRuleAdmin(admin.ModelAdmin):
    list_display = ("rate_percentage", "fixed_fee", "country", "category", "is_active", "valid_from")
    list_filter = ("is_active", "country")


@admin.register(PlatformTransaction)
class PlatformTransactionAdmin(admin.ModelAdmin):
    list_display = ("order", "gross_amount", "commission_rate", "commission_amount", "net_merchant_amount", "created_at")
    list_filter = ("status",)
