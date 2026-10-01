from django.contrib import admin
from django.utils import timezone
from .models import MerchantProfile, MerchantVerification, VerificationStatus


@admin.action(description="✓ Valider et attribuer le badge Commerçant Vérifié")
def approve_selected_merchants(modeladmin, request, queryset):
    updated = queryset.update(
        verification_status=VerificationStatus.VERIFIED,
        verified_at=timezone.now(),
    )
    modeladmin.message_user(request, f"{updated} profil(s) commerçant(s) validé(s) avec succès.")


@admin.action(description="✕ Rejeter la vérification des commerçants sélectionnés")
def reject_selected_merchants(modeladmin, request, queryset):
    updated = queryset.update(
        verification_status=VerificationStatus.REJECTED,
        rejection_reason="Pièces justificatives incomplètes ou non conformes.",
    )
    modeladmin.message_user(request, f"{updated} profil(s) commerçant(s) rejeté(s).")


class MerchantVerificationInline(admin.TabularInline):
    model = MerchantVerification
    extra = 0
    readonly_fields = ("submitted_at",)


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "user", "verification_status", "is_active", "verified_at")
    list_filter = ("verification_status", "is_active")
    search_fields = ("business_name", "user__email", "user__phone", "registration_number")
    actions = [approve_selected_merchants, reject_selected_merchants]
    inlines = [MerchantVerificationInline]


@admin.register(MerchantVerification)
class MerchantVerificationAdmin(admin.ModelAdmin):
    list_display = ("merchant", "document_type", "status", "submitted_at", "reviewed_at")
    list_filter = ("status", "document_type")
    search_fields = ("merchant__business_name", "document_type")
