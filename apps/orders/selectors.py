from django.core.exceptions import PermissionDenied
from .models import Order


def get_order_by_number(order_number, user=None):
    order = (
        Order.objects.filter(order_number=order_number)
        .select_related(
            "buyer",
            "campaign",
            "campaign__merchant",
            "campaign__product__store",
            "currency",
            "shipment",
        )
        .prefetch_related("items__product", "status_history")
        .first()
    )

    if not order:
        return None

    # Contrôle d'accès strict (Anti-IDOR)
    if user:
        if getattr(user, "is_admin", False) or user.is_superuser:
            return order

        is_buyer = order.buyer_id == user.id
        is_merchant = (
            order.campaign
            and order.campaign.merchant
            and order.campaign.merchant.user_id == user.id
        )

        if not (is_buyer or is_merchant):
            raise PermissionDenied("Vous n'avez pas l'autorisation de consulter cette commande.")

    return order


def list_user_orders(user):
    if not user or not user.is_authenticated:
        return Order.objects.none()

    return (
        Order.objects.filter(buyer=user)
        .select_related("currency", "campaign__product")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )


def list_merchant_orders(merchant, status=None):
    if not merchant:
        return Order.objects.none()

    qs = (
        Order.objects.filter(campaign__merchant=merchant)
        .select_related("buyer", "currency", "campaign__product")
        .prefetch_related("items__product")
    )

    if status:
        qs = qs.filter(status=status)

    return qs.order_by("-created_at")
