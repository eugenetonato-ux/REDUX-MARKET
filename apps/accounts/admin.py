from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, BuyerProfile


class BuyerProfileInline(admin.StackedInline):
    model = BuyerProfile
    can_delete = False
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "phone", "full_name", "role", "country", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "country")
    search_fields = ("email", "phone", "full_name")
    ordering = ("-date_joined",)
    inlines = [BuyerProfileInline]

    fieldsets = (
        (None, {"fields": ("email", "phone", "password")}),
        ("Informations personnelles", {"fields": ("full_name", "country")}),
        ("Rôle & Statut", {"fields": ("role", "email_verified", "phone_verified", "is_active", "is_staff", "is_superuser")}),
        ("Permissions & Groupes", {"fields": ("groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone", "role", "password1", "password2"),
        }),
    )
