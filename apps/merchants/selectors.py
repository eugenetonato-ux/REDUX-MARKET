from .models import MerchantProfile, MerchantVerification, VerificationStatus


def get_merchant_by_user(user):
    if not user or not user.is_authenticated:
        return None
    return MerchantProfile.objects.filter(user=user).first()


def get_merchant_stats(merchant):
    if not merchant:
        return {
            "stores_count": 0,
            "campaigns_count": 0,
            "orders_count": 0,
            "is_verified": False,
        }

    stores_count = merchant.stores.filter(is_active=True).count()
    campaigns_count = merchant.campaigns.count()
    # Count orders on stores belonging to this merchant
    orders_count = 0
    return {
        "stores_count": stores_count,
        "campaigns_count": campaigns_count,
        "orders_count": orders_count,
        "is_verified": merchant.is_verified,
        "verification_status": merchant.verification_status,
    }
