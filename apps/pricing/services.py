from decimal import Decimal
from apps.core.models import AuditLog
from .calculators import calculate_current_price
from .models import PriceTier
from .validators import validate_price_tiers


def create_price_tiers_for_campaign(campaign, tiers_data, user=None):
    product = campaign.product
    validate_price_tiers(
        tiers_data=tiers_data,
        minimum_price=product.minimum_price,
        original_price=product.original_price,
    )

    campaign.tiers.all().delete()
    created_tiers = []

    for t in tiers_data:
        price = Decimal(str(t["price"]))
        # Calculate discount percentage relative to original_price
        discount_pct = Decimal("0.00")
        if product.original_price > 0:
            discount_pct = ((product.original_price - price) / product.original_price) * Decimal("100")

        tier = PriceTier.objects.create(
            campaign=campaign,
            min_participants=t["min_participants"],
            max_participants=t.get("max_participants"),
            price=price,
            discount_percentage=round(discount_pct, 2),
        )
        created_tiers.append(tier)

    # Initialiser le prix courant de la campagne
    campaign.current_price = calculate_current_price(
        tiers=created_tiers,
        participant_count=campaign.current_participants_count,
        fallback_price=product.original_price,
    )
    campaign.save(update_fields=["current_price"])

    AuditLog.objects.create(
        actor=user or campaign.merchant.user,
        action="CAMPAIGN_TIERS_CONFIGURED",
        content_object=campaign,
        changes={"tiers_count": len(created_tiers), "initial_price": str(campaign.current_price)},
    )
    return created_tiers
