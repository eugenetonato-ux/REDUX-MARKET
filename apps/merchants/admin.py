from django.contrib import admin
from django.utils import timezone
from .models import MerchantProfile, MerchantVerification, VerificationStatus


@admin.action(description="Valider et attribuer le badge Commercant Verifie")
def approve_selected_merchants(modeladmin, request, queryset):
    from .verification import notify_merchant_kyc_approved
    count = 0
    for merchant in queryset.select_related("user"):
        if merchant.verification_status != VerificationStatus.VERIFIED:
            merchant.verification_status = VerificationStatus.VERIFIED
            merchant.verified_at = timezone.now()
            merchant.save(update_fields=["verification_status", "verified_at"])
            try:
                notify_merchant_kyc_approved(merchant)
            except Exception:
                pass
            count += 1
    modeladmin.message_user(request, f"{count} profil(s) commercant(s) valide(s) - notifications envoyees.")


@admin.action(description="Rejeter la verification des commercants selectionnes")
def reject_selected_merchants(modeladmin, request, queryset):
    from .verification import notify_merchant_kyc_rejected
    count = 0
    for merchant in queryset.select_related("user"):
        if merchant.verification_status != VerificationStatus.REJECTED:
            merchant.verification_status = VerificationStatus.REJECTED
            merchant.rejection_reason = "Pieces justificatives incompletes ou non conformes."
            merchant.save(update_fields=["verification_status", "rejection_reason"])
            try:
                notify_merchant_kyc_rejected(
                    merchant,
                    reason="Pieces justificatives incompletes ou non conformes."
                )
            except Exception:
                pass
            count += 1
    modeladmin.message_user(request, f"{count} profil(s) commercant(s) rejete(s) - notifications envoyees.")


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
