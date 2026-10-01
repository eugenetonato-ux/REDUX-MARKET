from django.contrib import admin
from .models import Dispute, DisputeMessage


class DisputeMessageInline(admin.TabularInline):
    model = DisputeMessage
    extra = 0


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "opened_by", "reason", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("order__order_number", "opened_by__email", "reason")
    inlines = [DisputeMessageInline]
