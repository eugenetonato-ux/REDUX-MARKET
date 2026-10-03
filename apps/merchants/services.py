from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from apps.core.models import AuditLog
from .models import MerchantProfile, MerchantVerification, VerificationStatus


def create_merchant_profile(user, business_name, business_type="", registration_number="", tax_id=""):
    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentification requise.")

    if hasattr(user, "merchant_profile") and user.merchant_profile:
        return user.merchant_profile

    profile = MerchantProfile.objects.create(
        user=user,
        business_name=business_name,
        business_type=business_type,
        registration_number=registration_number,
        tax_id=tax_id,
        verification_status=VerificationStatus.PENDING,
    )

    AuditLog.objects.create(
        actor=user,
        action="MERCHANT_PROFILE_CREATED",
        content_object=profile,
        changes={"business_name": business_name, "status": VerificationStatus.PENDING},
    )
    return profile


def submit_verification_document(merchant, document_type, document_file, user=None):
    if not merchant:
        raise ValidationError("Commerçant invalide.")

    verification = MerchantVerification.objects.create(
        merchant=merchant,
        document_type=document_type,
        document_file=document_file,
        status=VerificationStatus.PENDING,
    )

    if merchant.verification_status != VerificationStatus.VERIFIED:
        merchant.verification_status = VerificationStatus.PENDING
        merchant.save(update_fields=["verification_status"])

    AuditLog.objects.create(
        actor=user or merchant.user,
        action="VERIFICATION_DOCUMENT_SUBMITTED",
        content_object=verification,
        changes={"document_type": document_type},
    )

    # Accusé de réception au commerçant + alerte aux admins
    try:
        from .verification import notify_merchant_kyc_document_received, notify_admin_kyc_pending
        notify_merchant_kyc_document_received(merchant, document_type)
        notify_admin_kyc_pending(merchant, document_type)
    except Exception:
        pass

    return verification


def review_merchant_verification(verification_id, status, reviewer_notes="", admin_user=None):
    # Security Rule: Only admin can review and verify
    if not admin_user or not getattr(admin_user, "is_admin", False):
        raise PermissionDenied("Seul un administrateur peut valider la vérification.")

    if status not in [VerificationStatus.VERIFIED, VerificationStatus.REJECTED]:
        raise ValidationError("Statut invalide.")

    verification = MerchantVerification.objects.select_related("merchant").get(pk=verification_id)
    verification.status = status
    verification.reviewer_notes = reviewer_notes
    verification.reviewed_at = timezone.now()
    verification.save()

    merchant = verification.merchant
    if status == VerificationStatus.VERIFIED:
        merchant.verification_status = VerificationStatus.VERIFIED
        merchant.verified_at = timezone.now()
        merchant.save(update_fields=["verification_status", "verified_at"])
    elif status == VerificationStatus.REJECTED:
        merchant.verification_status = VerificationStatus.REJECTED
        merchant.rejection_reason = reviewer_notes
        merchant.save(update_fields=["verification_status", "rejection_reason"])

    AuditLog.objects.create(
        actor=admin_user,
        action=f"MERCHANT_VERIFICATION_{status}",
        content_object=merchant,
        changes={"status": status, "notes": reviewer_notes},
    )

    # Notification in-app + email au commerçant
    try:
        from .verification import notify_merchant_kyc_approved, notify_merchant_kyc_rejected
        if status == VerificationStatus.VERIFIED:
            notify_merchant_kyc_approved(merchant)
        elif status == VerificationStatus.REJECTED:
            notify_merchant_kyc_rejected(merchant, reason=reviewer_notes)
    except Exception:
        pass

    return verification
