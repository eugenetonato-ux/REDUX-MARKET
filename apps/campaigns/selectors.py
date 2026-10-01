from decimal import Decimal
from django.db.models import Q
from apps.pricing.calculators import calculate_current_tier, calculate_savings, get_next_tier, get_remaining_participants
from .models import Campaign, CampaignStatus


def list_active_campaigns(category_slug=None, country=None, search=None):
    # Only ACTIVE or TARGET_REACHED are public
    qs = Campaign.objects.filter(
        status__in=[CampaignStatus.ACTIVE, CampaignStatus.TARGET_REACHED]
    ).select_related(
        "product",
        "merchant",
        "product__store",
        "product__category",
        "product__store__country",
        "product__store__country__currency",
    ).prefetch_related("tiers", "product__images")

    if category_slug:
        qs = qs.filter(Q(product__category__slug=category_slug) | Q(product__category__parent__slug=category_slug))

    if country:
        qs = qs.filter(product__store__country=country)

    if search:
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(product__name__icontains=search)
            | Q(merchant__business_name__icontains=search)
        )

    return qs.order_by("-created_at")


def get_campaign_by_slug(slug):
    return (
        Campaign.objects.filter(slug=slug)
        .select_related(
            "product",
            "merchant",
            "creator",
            "product__store",
            "product__category",
            "product__store__country",
            "product__store__country__currency",
        )
        .prefetch_related("tiers", "product__images", "participants")
        .first()
    )


def get_campaign_summary(campaign):
    if not campaign:
        return {}

    tiers = list(campaign.tiers.all().order_by("min_participants"))
    current_count = campaign.current_participants_count
    current_tier = calculate_current_tier(tiers, current_count)
    next_tier = get_next_tier(tiers, current_count)
    remaining_for_next = get_remaining_participants(tiers, current_count)
    saved_amount, saved_pct = calculate_savings(campaign.product.original_price, campaign.current_price)

    # Progress percentage towards target
    target = campaign.target_participants
    progress_pct = min(100, int((current_count / target) * 100)) if target > 0 else 0

    return {
        "current_tier": current_tier,
        "next_tier": next_tier,
        "remaining_for_next": remaining_for_next,
        "saved_amount": saved_amount,
        "saved_pct": saved_pct,
        "progress_pct": progress_pct,
        "currency": campaign.product.store.country.currency,
    }
