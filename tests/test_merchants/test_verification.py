import pytest
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.countries.models import Country, Currency
from apps.merchants.models import VerificationStatus
from apps.merchants.services import (
    create_merchant_profile,
    review_merchant_verification,
    submit_verification_document,
)
from apps.stores.services import create_store


@pytest.mark.django_db
def test_merchant_profile_creation_is_pending_by_default():
    user = User.objects.create_user(email="merchant@redux.app", password="password123", role=UserRole.MERCHANT)
    merchant = create_merchant_profile(user, business_name="Boutique Cotonou Tech")

    assert merchant.verification_status == VerificationStatus.PENDING
    assert merchant.is_verified is False
    assert merchant.verified_at is None


@pytest.mark.django_db
def test_non_admin_cannot_review_verification():
    merchant_user = User.objects.create_user(email="seller@redux.app", password="password123", role=UserRole.MERCHANT)
    merchant = create_merchant_profile(merchant_user, business_name="Seller Tech")

    fake_file = SimpleUploadedFile("rccm.pdf", b"dummy content", content_type="application/pdf")
    verification = submit_verification_document(merchant, "RCCM", fake_file)

    # Merchant cannot review their own verification
    with pytest.raises(PermissionDenied):
        review_merchant_verification(
            verification_id=verification.id,
            status=VerificationStatus.VERIFIED,
            admin_user=merchant_user,
        )


@pytest.mark.django_db
def test_admin_can_verify_merchant():
    admin_user = User.objects.create_superuser(email="admin@redux.app", password="password123")
    merchant_user = User.objects.create_user(email="vendeur@redux.app", password="password123", role=UserRole.MERCHANT)
    merchant = create_merchant_profile(merchant_user, business_name="Vendeur Pro")

    fake_file = SimpleUploadedFile("ifu.pdf", b"dummy content", content_type="application/pdf")
    verification = submit_verification_document(merchant, "IFU", fake_file)

    reviewed = review_merchant_verification(
        verification_id=verification.id,
        status=VerificationStatus.VERIFIED,
        reviewer_notes="Documents complets et authentiques.",
        admin_user=admin_user,
    )

    merchant.refresh_from_db()
    assert reviewed.status == VerificationStatus.VERIFIED
    assert merchant.verification_status == VerificationStatus.VERIFIED
    assert merchant.is_verified is True
    assert merchant.verified_at is not None


@pytest.mark.django_db
def test_store_creation_with_unique_slug():
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "CFA"})
    country, _ = Country.objects.get_or_create(code="BJ", defaults={"name": "Bénin", "phone_prefix": "+229", "currency": currency})
    user = User.objects.create_user(email="storeowner@redux.app", password="password123", role=UserRole.MERCHANT)
    merchant = create_merchant_profile(user, business_name="Super Shop")

    store1 = create_store(merchant, country, name="Super Shop")
    store2 = create_store(merchant, country, name="Super Shop")

    assert store1.slug == "super-shop"
    assert store2.slug == "super-shop-1"
    assert store1.is_active is True
