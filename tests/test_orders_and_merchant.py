from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from apps.accounts.roles import UserRole
from apps.campaigns.models import Campaign, CampaignParticipant, CampaignStatus, PricingPolicy
from apps.catalog.models import Category, Product
from apps.countries.models import Country, Currency
from apps.orders.models import Order, OrderStatus
from apps.payments.models import Payment, PaymentStatus
from apps.pricing.models import PriceTier
from apps.stores.models import Store

User = get_user_model()


@pytest.fixture
def setup_data(db):
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "FCFA"})
    country, _ = Country.objects.get_or_create(
        code="BJ",
        defaults={"name": "Bénin", "phone_prefix": "+229", "flag_emoji": "🇧🇯", "currency": currency, "is_active": True},
    )

    # Acheteur
    buyer = User.objects.create_user(
        email="buyer.test@redux.africa",
        phone="+22997001122",
        password="Password123!",
        role=UserRole.BUYER,
        country=country,
    )

    # Commerçant
    merchant_user = User.objects.create_user(
        email="merchant.test@redux.africa",
        phone="+22997112244",
        password="Password123!",
        role=UserRole.MERCHANT,
        country=country,
    )
    from apps.merchants.models import MerchantProfile, VerificationStatus
    merchant_profile = MerchantProfile.objects.create(
        user=merchant_user,
        business_name="Boutique Test",
        verification_status=VerificationStatus.VERIFIED,
        is_active=True,
    )
    store = Store.objects.create(
        merchant=merchant_profile,
        country=country,
        name="Store Test",
        slug="store-test",
        is_active=True,
    )

    # Catégorie & Produit
    cat = Category.objects.create(name="Tech", slug="tech", is_active=True)
    product = Product.objects.create(
        store=store,
        category=cat,
        name="Produit Test",
        slug="produit-test",
        original_price=Decimal("20000.00"),
        minimum_price=Decimal("12000.00"),
        stock=50,
        is_active=True,
    )

    # Campagne
    from django.utils import timezone
    from datetime import timedelta
    now = timezone.now()
    campaign = Campaign.objects.create(
        product=product,
        merchant=merchant_profile,
        creator=merchant_user,
        title="Campagne Test Groupée",
        slug="campagne-test-groupee",
        status=CampaignStatus.ACTIVE,
        pricing_policy=PricingPolicy.FINAL_TIER_PRICE,
        min_participants=2,
        target_participants=10,
        current_participants_count=3,
        current_price=Decimal("16000.00"),
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=10),
    )
    PriceTier.objects.create(campaign=campaign, min_participants=1, max_participants=4, price=Decimal("18000.00"))
    PriceTier.objects.create(campaign=campaign, min_participants=5, max_participants=9, price=Decimal("16000.00"))
    PriceTier.objects.create(campaign=campaign, min_participants=10, max_participants=None, price=Decimal("13000.00"))

    return {
        "buyer": buyer,
        "merchant_user": merchant_user,
        "merchant_profile": merchant_profile,
        "store": store,
        "category": cat,
        "product": product,
        "campaign": campaign,
    }


@pytest.mark.django_db
def test_full_checkout_and_payment_flow(client: Client, setup_data):
    """
    Test du tunnel complet (Étape 3) :
    Participation -> Checkout -> Commande PENDING -> Choix Paiement -> Simulation webhook séquestre -> Commande PAID
    """
    buyer = setup_data["buyer"]
    campaign = setup_data["campaign"]

    # Connexion de l'acheteur
    client.force_login(buyer)

    # 1. Participation
    resp_join = client.post(f"/campaigns/{campaign.slug}/join/", {"quantity": 2}, follow=True)
    assert resp_join.status_code == 200

    part = CampaignParticipant.objects.get(campaign=campaign, user=buyer)
    assert part.quantity == 2

    # 2. Checkout
    resp_checkout = client.get(f"/checkout/{part.id}/")
    assert resp_checkout.status_code == 200

    payload_order = {
        "shipping_address": "Rue 12, Lot 45, Cotonou, Bénin",
        "contact_phone": "+229 97 00 11 22",
    }
    resp_create_order = client.post(f"/checkout/{part.id}/", payload_order, follow=True)
    assert resp_create_order.status_code == 200

    order = Order.objects.get(campaign_participant=part)
    assert order.status == OrderStatus.PENDING
    assert order.shipping_address == payload_order["shipping_address"]

    # 3. Page de sélection de paiement
    resp_payment_page = client.get(f"/payment/?order={order.order_number}")
    assert resp_payment_page.status_code == 200
    assert "Moyens de paiement disponibles" in resp_payment_page.content.decode()

    # 4. Initiation du paiement Mobile Money
    resp_init_pay = client.post(
        "/payment/",
        {"order": order.order_number, "payment_method": "mtn_momo", "provider": "mock"},
        follow=True,
    )
    assert resp_init_pay.status_code == 200
    assert f"/payment/pending/{order.order_number}/" in resp_init_pay.redirect_chain[0][0]

    # 5. Simulation confirmation webhook
    resp_simulate = client.post(
        f"/payment/pending/{order.order_number}/",
        {"simulate_confirm": "1"},
        follow=True,
    )
    assert resp_simulate.status_code == 200
    assert f"/payment/success/{order.order_number}/" in resp_simulate.redirect_chain[0][0]

    # Vérification que la commande est désormais PAYÉE
    order.refresh_from_db()
    assert order.status == OrderStatus.PAID


@pytest.mark.django_db
def test_merchant_portal_full_workflow(client: Client, setup_data):
    """
    Test de l'Espace Commerçant (Étape 4) :
    Dashboard -> Ajout Produit -> Création Campagne Paliers -> Suivi Commandes -> Expédition
    """
    merchant_user = setup_data["merchant_user"]
    store = setup_data["store"]
    cat = setup_data["category"]

    client.force_login(merchant_user)

    # 1. Dashboard commerçant
    resp_dash = client.get("/merchant/dashboard/")
    assert resp_dash.status_code == 200
    assert "Tableau de Bord Commerçant" in resp_dash.content.decode()

    # 2. Liste et création de produit
    resp_prods = client.get("/merchant/products/")
    assert resp_prods.status_code == 200

    new_prod_payload = {
        "name": "Machine à Laver Nasco 7kg",
        "category": cat.id,
        "description": "Lave-linge automatique économe",
        "original_price": "180000.00",
        "minimum_price": "140000.00",
        "stock": 20,
        "unit": "pièce",
    }
    resp_create_prod = client.post("/merchant/products/create/", new_prod_payload, follow=True)
    assert resp_create_prod.status_code == 200
    assert Product.objects.filter(name="Machine à Laver Nasco 7kg").exists()

    created_prod = Product.objects.get(name="Machine à Laver Nasco 7kg")

    # 3. Création d'une campagne collective avec paliers
    campaign_payload = {
        "product": created_prod.id,
        "title": "Achat Groupé : Machine à Laver Nasco 7kg",
        "pricing_policy": PricingPolicy.FINAL_TIER_PRICE,
        "target_participants": 15,
        "days_duration": 14,
        "terms": "Garantie 2 ans",
        "tier_min[]": ["1", "5", "10"],
        "tier_max[]": ["4", "9", ""],
        "tier_price[]": ["180000.00", "160000.00", "145000.00"],
    }
    resp_create_camp = client.post("/merchant/campaigns/create/", campaign_payload, follow=True)
    assert resp_create_camp.status_code == 200

    new_camp = Campaign.objects.get(title="Achat Groupé : Machine à Laver Nasco 7kg")
    assert new_camp.tiers.count() == 3

    # 4. Commandes commerçant & mise à jour du statut d'expédition
    order = Order.objects.create(
        order_number="ORD-TEST-999",
        buyer=setup_data["buyer"],
        campaign=new_camp,
        currency=store.country.currency,
        total_amount=Decimal("145000.00"),
        final_amount=Decimal("145000.00"),
        status=OrderStatus.PAID,
        shipping_address="Cotonou Haie Vive",
        contact_phone="+22997001122",
    )

    resp_orders = client.get("/merchant/orders/")
    assert resp_orders.status_code == 200
    assert "ORD-TEST-999" in resp_orders.content.decode()

    # Mise à jour du statut vers EXPÉDIÉE
    resp_ship = client.post(
        f"/merchant/orders/{order.order_number}/",
        {"status": OrderStatus.SHIPPED, "notes": "Colis remis au livreur Express"},
        follow=True,
    )
    assert resp_ship.status_code == 200
    order.refresh_from_db()
    assert order.status == OrderStatus.SHIPPED

    # 5. Consultation des revenus et statistiques
    resp_rev = client.get("/merchant/revenue/")
    assert resp_rev.status_code == 200

    resp_stats = client.get("/merchant/statistics/")
    assert resp_stats.status_code == 200
