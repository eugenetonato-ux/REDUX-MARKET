from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "title", "notification_type", "is_read", "created_at")
    list_filter = ("is_read", "notification_type")
    search_fields = ("recipient__email", "title", "message")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "email_notifications", "sms_notifications", "whatsapp_notifications", "in_app_notifications")
