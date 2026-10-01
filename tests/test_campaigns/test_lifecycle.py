from datetime import timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.campaigns.models import CampaignStatus
from apps.campaigns.services import create_campaign, join_campaign
from apps.campaigns.state_machine import transition_campaign_status
from apps.catalog.services import create_product
from apps.countries.models import Country, Currency
from apps.merchants.models import VerificationStatus
from apps.merchants.services import create_merchant_profile
from apps.stores.services import create_store


@pytest.fixture
def campaign_setup():
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "CFA"})
    country, _ = Country.objects.get_or_create(code="BJ", defaults={"name": "Bénin", "phone_prefix": "+229", "currency": currency})

    merchant_user = User.objects.create_user(email="merchant_camp@redux.app", password="password123", role=UserRole.MERCHANT)
    merchant = create_merchant_profile(merchant_user, business_name="Électro Bénin")
    merchant.verification_status = VerificationStatus.VERIFIED
    merchant.save()

    store = create_store(merchant, country, name="Électro Cotonou")
    product = create_product(
        store=store,
        name="Écouteurs Sans Fil Pro",
        original_price="25000",
        minimum_price="15000",
        stock=50,
    )

    buyer = User.objects.create_user(email="buyer1@redux.app", password="password123", role=UserRole.BUYER)

    tiers_data = [
        {"min_participants": 2, "max_participants": 5, "price": "22000"},
        {"min_participants": 6, "max_participants": 10, "price": "19000"},
        {"min_participants": 11, "max_participants": None, "price": "16000"},
    ]

    now = timezone.now()
    campaign = create_campaign(
        product=product,
        creator=buyer,
        merchant=merchant,
        title="Groupe Écouteurs Pro Cotonou",
        target_participants=6,
        min_participants=2,
        max_participants=20,
        start_date=now,
        end_date=now + timedelta(days=7),
        tiers_data=tiers_data,
    )

    return {
        "campaign": campaign,
        "buyer": buyer,
        "product": product,
        "merchant": merchant,
    }


@pytest.mark.django_db
def test_campaign_created_active_if_verified(campaign_setup):
    campaign = campaign_setup["campaign"]
    assert campaign.status == CampaignStatus.ACTIVE
    assert campaign.current_participants_count == 0
    assert campaign.current_price == Decimal("25000")  # Original price before reaching tier 1


@pytest.mark.django_db
def test_join_campaign_updates_participants_and_price(campaign_setup):
    campaign = campaign_setup["campaign"]
    buyer1 = campaign_setup["buyer"]
    buyer2 = User.objects.create_user(email="buyer2@redux.app", password="password123", role=UserRole.BUYER)

    # First participant joins
    part1 = join_campaign(campaign, buyer1, quantity=1)
    campaign.refresh_from_db()
    assert campaign.current_participants_count == 1
    assert part1.unit_price == Decimal("25000")

    # Second participant joins -> reaches Tier 1 (starts at 2 participants: 22000 XOF)
    part2 = join_campaign(campaign, buyer2, quantity=1)
    campaign.refresh_from_db()
    assert campaign.current_participants_count == 2
    assert campaign.current_price == Decimal("22000")
    assert part2.unit_price == Decimal("22000")


@pytest.mark.django_db
def test_user_cannot_join_twice_actively(campaign_setup):
    campaign = campaign_setup["campaign"]
    buyer = campaign_setup["buyer"]

    join_campaign(campaign, buyer, quantity=1)

    # Joining again should raise ValidationError
    with pytest.raises(ValidationError, match="Vous participez déjà activement"):
        join_campaign(campaign, buyer, quantity=1)


@pytest.mark.django_db
def test_state_machine_invalid_transition(campaign_setup):
    campaign = campaign_setup["campaign"]
    assert campaign.status == CampaignStatus.ACTIVE

    # ACTIVE cannot jump directly to SUCCESS without TARGET_REACHED or PAYMENT_PENDING
    with pytest.raises(ValidationError, match="Transition de statut interdite"):
        transition_campaign_status(campaign, CampaignStatus.SUCCESS)
