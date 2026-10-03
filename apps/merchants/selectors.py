from decimal import Decimal
from django.db.models import Count, Sum
from apps.campaigns.models import Campaign, CampaignParticipant, CampaignStatus
from apps.orders.models import Order, OrderStatus
from .models import MerchantProfile, MerchantVerification, VerificationStatus


def get_merchant_by_user(user):
    if not user or not user.is_authenticated:
        return None
    return MerchantProfile.objects.filter(user=user).select_related("user").first()


def get_merchant_stats(merchant):
    if not merchant:
        return {
            "stores_count": 0,
            "campaigns_count": 0,
            "orders_count": 0,
            "total_sales": Decimal("0.00"),
            "net_revenue": Decimal("0.00"),
            "total_participants": 0,
            "is_verified": False,
            "verification_status": VerificationStatus.PENDING,
        }

    stores_count = merchant.stores.filter(is_active=True).count()
    campaigns = merchant.campaigns.all()
    campaigns_count = campaigns.count()
    active_campaigns_count = campaigns.filter(status__in=[CampaignStatus.ACTIVE, CampaignStatus.TARGET_REACHED]).count()

    # Commandes liées aux campagnes de ce commerçant
    merchant_orders = Order.objects.filter(campaign__merchant=merchant)
    orders_count = merchant_orders.count()
    paid_orders = merchant_orders.filter(status__in=[OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED])

    # Volume total des ventes payées
    total_sales = paid_orders.aggregate(total=Sum("final_amount"))["total"] or Decimal("0.00")

    # Commission plateforme standard 5%
    commission_rate = Decimal("0.05")
    platform_commission = (total_sales * commission_rate).quantize(Decimal("0.01"))
    net_revenue = total_sales - platform_commission

    # Total des participants à travers toutes les campagnes du commerçant
    total_participants = CampaignParticipant.objects.filter(campaign__merchant=merchant).count()

    return {
        "stores_count": stores_count,
        "campaigns_count": campaigns_count,
        "active_campaigns_count": active_campaigns_count,
        "orders_count": orders_count,
        "paid_orders_count": paid_orders.count(),
        "total_sales": total_sales,
        "platform_commission": platform_commission,
        "net_revenue": net_revenue,
        "total_participants": total_participants,
        "is_verified": merchant.is_verified,
        "verification_status": merchant.verification_status,
    }
