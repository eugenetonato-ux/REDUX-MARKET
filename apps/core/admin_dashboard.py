from decimal import Decimal
from django.db.models import Sum
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.campaigns.models import Campaign, CampaignStatus
from apps.commissions.models import PlatformTransaction
from apps.merchants.models import MerchantProfile, MerchantVerification, VerificationStatus
from apps.orders.models import Order, OrderStatus
from apps.stores.models import Store


def get_platform_metrics():
    total_buyers = User.objects.filter(role=UserRole.BUYER).count()
    total_merchants = User.objects.filter(role=UserRole.MERCHANT).count()
    pending_verifications = MerchantVerification.objects.filter(status=VerificationStatus.PENDING).count()

    total_stores = Store.objects.filter(is_active=True).count()
    active_campaigns = Campaign.objects.filter(status=CampaignStatus.ACTIVE).count()

    paid_statuses = [
        OrderStatus.PAID,
        OrderStatus.PROCESSING,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
    ]
    paid_orders_qs = Order.objects.filter(status__in=paid_statuses)
    paid_orders_count = paid_orders_qs.count()

    gmv_result = paid_orders_qs.aggregate(total=Sum("final_amount"))
    total_gmv = gmv_result["total"] or Decimal("0.00")

    comm_result = PlatformTransaction.objects.aggregate(total=Sum("commission_amount"))
    total_commissions = comm_result["total"] or Decimal("0.00")

    return {
        "total_buyers": total_buyers,
        "total_merchants": total_merchants,
        "pending_verifications": pending_verifications,
        "total_stores": total_stores,
        "active_campaigns": active_campaigns,
        "total_orders": Order.objects.count(),
        "paid_orders": paid_orders_count,
        "total_gmv": total_gmv,
        "total_commissions": total_commissions,
    }
