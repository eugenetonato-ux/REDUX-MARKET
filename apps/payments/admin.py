from django.contrib import admin
from .models import PaymentProvider, Payment, PaymentTransaction, WebhookEvent, Refund


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("idempotency_key", "order", "provider", "amount", "currency", "status", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("idempotency_key", "reference", "order__order_number")


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("payment", "transaction_type", "amount", "status", "created_at")
    list_filter = ("status", "transaction_type")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "provider", "event_type", "processed", "created_at")
    list_filter = ("processed", "provider")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("order", "payment", "amount", "status", "created_at")
    list_filter = ("status",)
