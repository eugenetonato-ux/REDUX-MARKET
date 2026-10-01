from django.contrib import admin
from .models import AuditLog, PlatformSetting


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "content_type", "object_id", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("action", "actor__email", "actor__phone", "object_id")
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "is_public", "updated_at")
    search_fields = ("key", "description")
