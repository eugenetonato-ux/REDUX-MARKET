from datetime import timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.campaigns.models import CampaignParticipantStatus
from apps.campaigns.services import create_campaign, join_campaign
from apps.catalog.services import create_product
from apps.countries.models import Country, Currency
from apps.merchants.models import VerificationStatus
from apps.merchants.services import create_merchant_profile
from apps.orders.numbering import generate_order_number
from apps.orders.services import create_order_from_participation
from apps.stores.services import create_store


@pytest.fixture
def order_setup():
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "CFA"})
    country, _ = Country.objects.get_or_create(code="BJ", defaults={"name": "Bénin", "phone_prefix": "+229", "currency": currency})

    merchant_user = User.objects.create_user(email="order_merchant@redux.app", password="password123", role=UserRole.MERCHANT)
    merchant = create_merchant_profile(merchant_user, business_name="Boutique Cotonou Mall")
    merchant.verification_status = VerificationStatus.VERIFIED
    merchant.save()

    store = create_store(merchant, country, name="Cotonou Mall")
    product = create_product(
        store=store,
        name="Sac de Voyage Premium",
        original_price="40000",
        minimum_price="25000",
        stock=100,
    )

    buyer = User.objects.create_user(email="buyer_order@redux.app", password="password123", role=UserRole.BUYER)

    tiers = [
        {"min_participants": 2, "max_participants": 5, "price": "35000"},
        {"min_participants": 6, "max_participants": None, "price": "30000"},
    ]

    now = timezone.now()
    campaign = create_campaign(
        product=product,
        creator=buyer,
        merchant=merchant,
        title="Groupe Sacs de Voyage",
        target_participants=6,
        min_participants=2,
        max_participants=50,
        start_date=now,
        end_date=now + timedelta(days=5),
        tiers_data=tiers,
    )

    participant = join_campaign(campaign, buyer, quantity=2)
    return {
        "campaign": campaign,
        "participant": participant,
        "buyer": buyer,
        "product": product,
    }


@pytest.mark.django_db
def test_order_numbering_uniqueness_and_format():
    num1 = generate_order_number()
    num2 = generate_order_number()
    assert num1 != num2
    assert num1.startswith("RDX-")
    assert len(num1.split("-")) == 3


@pytest.mark.django_db
def test_create_order_from_participation(order_setup):
    participant = order_setup["participant"]
    buyer = order_setup["buyer"]

    order = create_order_from_participation(
        participant=participant,
        shipping_address="Cotonou, Haie Vive",
        contact_phone="+22997001122",
        delivery_fee=Decimal("1000.00"),
        user=buyer,
    )

    assert order.buyer == buyer
    assert order.order_number.startswith("RDX-")
    assert order.status == "PENDING"
    assert order.items.count() == 1
    # 2 units x tier price 35000 (reached Tier 1 at 2 units)
    assert order.total_amount == Decimal("70000.00")
    assert order.final_amount == Decimal("71000.00")  # 70000 + 1000 delivery

    participant.refresh_from_db()
    assert participant.status == CampaignParticipantStatus.CONFIRMED


@pytest.mark.django_db
def test_cannot_create_order_for_other_user_participation(order_setup):
    participant = order_setup["participant"]
    other_user = User.objects.create_user(email="intruder@redux.app", password="password123", role=UserRole.BUYER)

    with pytest.raises(PermissionDenied):
        create_order_from_participation(
            participant=participant,
            shipping_address="Quelque part",
            contact_phone="+22900000000",
            user=other_user,
        )


@pytest.mark.django_db
def test_order_status_transition_triggers_notification(order_setup):
    """Vérifie que changer le statut d'une commande génère une notification in-app pour l'acheteur."""
    from apps.orders.state_machine import transition_order_status
    buyer = order_setup["buyer"]
    participant = order_setup["participant"]

    order = create_order_from_participation(
        participant=participant,
        shipping_address="Cotonou, Haie Vive",
        contact_phone="+22997001122",
        delivery_fee=Decimal("1000.00"),
        user=buyer,
    )

    buyer.notifications.all().delete()
    assert buyer.notifications.count() == 0

    transition_order_status(order, "PAID")
    assert buyer.notifications.filter(notification_type="order_paid").exists()
    notif = buyer.notifications.filter(notification_type="order_paid").first()
    assert order.order_number in notif.title

    transition_order_status(order, "SHIPPED")
    assert buyer.notifications.filter(notification_type="order_shipped").exists()


@pytest.mark.django_db
def test_campaign_tier_unlock_triggers_notification(order_setup):
    """Vérifie que lorsqu'un palier inférieur est atteint, les participants reçoivent une alerte."""
    campaign = order_setup["campaign"]
    buyer2 = User.objects.create_user(email="buyer2_tier@redux.app", password="password123", role=UserRole.BUYER)

    # Avant l'arrivée de buyer2, la campagne a 2 participants.
    # Le palier suivant est min_participants=6 (30000 CFA).
    # buyer2 rejoint avec quantity=4 -> total = 6 participants -> débloque le palier 30000 CFA !
    join_campaign(campaign, buyer2, quantity=4)

    # L'acheteur initial doit avoir reçu une notification tier_reached
    buyer = order_setup["buyer"]
    assert buyer.notifications.filter(notification_type="tier_reached").exists()
    tier_notif = buyer.notifications.filter(notification_type="tier_reached").first()
    assert "30000" in tier_notif.message
