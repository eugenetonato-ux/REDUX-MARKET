from datetime import timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.countries.models import Country, Currency
from apps.merchants.models import MerchantProfile, VerificationStatus
from apps.purchase_requests.models import ProposalStatus, PurchaseRequest, RequestStatus, SellerProposal
from apps.purchase_requests.services import (
    accept_seller_proposal,
    create_purchase_request,
    create_seller_proposal,
    join_purchase_request,
)
from apps.stores.models import Store


@pytest.fixture
def country(db):
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "FCFA"})
    return Country.objects.create(
        code="BJ",
        name="Bénin",
        phone_prefix="+229",
        flag_emoji="🇧🇯",
        currency=currency,
        is_active=True,
    )


@pytest.fixture
def buyer_user(db):
    return User.objects.create_user(
        phone="+22997000001",
        email="buyer@test.app",
        password="ValidPassword123!",
        full_name="Amina Buyer",
        role=UserRole.BUYER,
    )


@pytest.fixture
def other_buyer(db):
    return User.objects.create_user(
        phone="+22997000002",
        email="buyer2@test.app",
        password="ValidPassword123!",
        full_name="Kofi Buyer2",
        role=UserRole.BUYER,
    )


@pytest.fixture
def verified_merchant(db, country):
    user = User.objects.create_user(
        phone="+22997000003",
        email="merchant@test.app",
        password="ValidPassword123!",
        full_name="Jean Merchant",
        role=UserRole.MERCHANT,
    )
    profile = MerchantProfile.objects.create(
        user=user,
        business_name="Grossiste Jean & Frères",
        verification_status=VerificationStatus.VERIFIED,
    )
    store = Store.objects.create(
        merchant=profile,
        country=country,
        name="Entrepôt Cotonou",
        slug="entrepot-cotonou",
        is_active=True,
    )
    return profile, store


@pytest.fixture
def unverified_merchant(db, country):
    user = User.objects.create_user(
        phone="+22997000004",
        email="unverified@test.app",
        password="ValidPassword123!",
        full_name="Paul Unverified",
        role=UserRole.MERCHANT,
    )
    profile = MerchantProfile.objects.create(
        user=user,
        business_name="Boutique Non Vérifiée",
        verification_status=VerificationStatus.PENDING,
    )
    store = Store.objects.create(
        merchant=profile,
        country=country,
        name="Boutique Paul",
        slug="boutique-paul",
        is_active=True,
    )
    return profile, store


@pytest.mark.django_db
def test_create_purchase_request_success(buyer_user, country):
    expires_at = timezone.now() + timedelta(days=14)
    req = create_purchase_request(
        creator=buyer_user,
        country=country,
        category=None,
        title="50 Sacs de Farine de Blé 50kg",
        description="Besoin pour coopérative de boulangerie",
        target_quantity=50,
        target_price=Decimal("18000.00"),
        expires_at=expires_at,
    )

    assert req.id is not None
    assert req.status == RequestStatus.OPEN
    assert req.participants.count() == 1
    pledge = req.participants.first()
    assert pledge.user == buyer_user
    assert pledge.quantity_pledged == 1


@pytest.mark.django_db
def test_create_purchase_request_validation(buyer_user, country):
    expires_at = timezone.now() + timedelta(days=14)

    # Quantité cible < 2
    with pytest.raises(ValidationError):
        create_purchase_request(
            creator=buyer_user,
            country=country,
            category=None,
            title="1 seul sac",
            description="Pas groupé",
            target_quantity=1,
            target_price=Decimal("1000.00"),
            expires_at=expires_at,
        )

    # Date passée
    with pytest.raises(ValidationError):
        create_purchase_request(
            creator=buyer_user,
            country=country,
            category=None,
            title="Demande expirée",
            description="Date passée",
            target_quantity=10,
            target_price=Decimal("1000.00"),
            expires_at=timezone.now() - timedelta(days=1),
        )


@pytest.mark.django_db
def test_join_purchase_request_and_prevent_duplicate(buyer_user, other_buyer, country):
    expires_at = timezone.now() + timedelta(days=14)
    req = create_purchase_request(
        creator=buyer_user,
        country=country,
        category=None,
        title="100 cartons de lait",
        description="Achat groupé lait",
        target_quantity=100,
        target_price=Decimal("5000.00"),
        expires_at=expires_at,
    )

    # Autre acheteur rejoint
    pledge = join_purchase_request(purchase_request=req, user=other_buyer, quantity_pledged=5)
    assert pledge.quantity_pledged == 5
    assert req.participants.count() == 2

    # Tentative d'adhésion en double => Doit lever ValidationError
    with pytest.raises(ValidationError, match="déjà"):
        join_purchase_request(purchase_request=req, user=other_buyer, quantity_pledged=2)


@pytest.mark.django_db
def test_unverified_merchant_cannot_propose(buyer_user, unverified_merchant, country):
    profile, store = unverified_merchant
    expires_at = timezone.now() + timedelta(days=14)
    req = create_purchase_request(
        creator=buyer_user,
        country=country,
        category=None,
        title="20 sacs de sucre",
        description="Besoin urgent",
        target_quantity=20,
        target_price=Decimal("20000.00"),
        expires_at=expires_at,
    )

    # Le marchand non vérifié doit être bloqué avec PermissionDenied
    with pytest.raises(PermissionDenied, match="vérifiés"):
        create_seller_proposal(
            purchase_request=req,
            merchant=profile,
            store=store,
            proposed_price=Decimal("19500.00"),
        )


@pytest.mark.django_db
def test_verified_merchant_proposal_and_creator_acceptance(buyer_user, other_buyer, verified_merchant, country):
    profile, store = verified_merchant
    expires_at = timezone.now() + timedelta(days=14)
    req = create_purchase_request(
        creator=buyer_user,
        country=country,
        category=None,
        title="30 bidons d'huile végétale 25L",
        description="Pour restauration collective",
        target_quantity=30,
        target_price=Decimal("22000.00"),
        expires_at=expires_at,
    )

    # Soumission de l'offre
    proposal = create_seller_proposal(
        purchase_request=req,
        merchant=profile,
        store=store,
        proposed_price=Decimal("21500.00"),
        min_quantity=10,
        description="Huile pure tournesol raffinée",
    )

    req.refresh_from_db()
    assert req.status == RequestStatus.PROPOSALS_RECEIVED
    assert proposal.status == ProposalStatus.PENDING

    # Tentative d'acceptation par un autre utilisateur non créateur
    with pytest.raises(PermissionDenied, match="initiateur"):
        accept_seller_proposal(purchase_request=req, proposal=proposal, user=other_buyer)

    # Acceptation par le créateur
    accepted = accept_seller_proposal(purchase_request=req, proposal=proposal, user=buyer_user)
    assert accepted.status == ProposalStatus.ACCEPTED

    req.refresh_from_db()
    assert req.status == RequestStatus.ACCEPTED


@pytest.mark.django_db
def test_purchase_request_views(client, buyer_user, country):
    # Liste publique
    resp = client.get("/requests/")
    assert resp.status_code == 200

    # Création connectée
    client.force_login(buyer_user)
    resp = client.post(
        "/requests/nouveau/",
        {
            "title": "50 casiers de boisson",
            "country": country.id,
            "description": "Fête de fin d'année",
            "target_quantity": 50,
            "target_price": "8000.00",
            "duration_days": "14",
        },
    )
    assert resp.status_code == 302
    req = PurchaseRequest.objects.get(title="50 casiers de boisson")
    assert req.creator == buyer_user

    # Détail
    resp = client.get(f"/requests/{req.id}/")
    assert resp.status_code == 200
    assert "50 casiers de boisson" in resp.content.decode()
