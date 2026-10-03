from decimal import Decimal
import pytest
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.campaigns.models import Campaign, CampaignStatus
from apps.catalog.models import Category, Product
from apps.countries.models import Country, Currency
from apps.disputes.models import Dispute, DisputeMessage, DisputeStatus
from apps.notifications.models import Notification
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.purchase_requests.models import PurchaseRequest, RequestStatus
from apps.reviews.models import Review
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
def merchant_user(db):
    return User.objects.create_user(
        phone="+22997000001",
        email="merchant5@test.app",
        password="Password123!",
        full_name="Merchant Test",
        role=UserRole.MERCHANT,
    )


from apps.merchants.models import MerchantProfile


@pytest.fixture
def merchant_profile(db, merchant_user):
    return MerchantProfile.objects.create(
        user=merchant_user,
        business_name="Tech Store SARL",
    )


@pytest.fixture
def store(db, merchant_profile, country):
    return Store.objects.create(
        merchant=merchant_profile,
        name="Tech Boutique Étape 5",
        slug="tech-boutique-etape-5",
        country=country,
        city="Cotonou",
        address="Akpakpa",
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name="Audio & Musique", slug="audio-musique")


@pytest.fixture
def product(db, store, category):
    return Product.objects.create(
        store=store,
        category=category,
        name="Casque Hi-Fi Pro",
        slug="casque-hifi-pro",
        description="Casque sans fil de haute qualité audio.",
        original_price=Decimal("45000"),
        minimum_price=Decimal("30000"),
        stock=50,
        is_active=True,
    )


@pytest.fixture
def buyer_user(db):
    return User.objects.create_user(
        phone="+22997000002",
        email="buyer5@test.app",
        password="Password123!",
        full_name="Buyer Test 5",
        role=UserRole.BUYER,
    )


@pytest.fixture
def paid_order(db, buyer_user, product, country):
    order = Order.objects.create(
        buyer=buyer_user,
        order_number="ORD-TEST-E5-001",
        status=OrderStatus.PAID,
        total_amount=Decimal("35000"),
        final_amount=Decimal("35000"),
        shipping_address="Cotonou, Quartier Haie Vive",
        contact_phone="+22997000002",
        currency=country.currency,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        unit_price=Decimal("35000"),
        total_price=Decimal("35000"),
    )
    return order


@pytest.mark.django_db
class TestPurchaseRequestsViews:
    def test_list_and_detail_views(self, client, buyer_user, category, country):
        req = PurchaseRequest.objects.create(
            creator=buyer_user,
            category=category,
            country=country,
            title="Recherche Lot Rame Papier A4",
            description="Besoin de 50 cartons de ramettes A4 pour bureau.",
            target_price=Decimal("15000"),
            target_quantity=50,
            expires_at=timezone.now() + timezone.timedelta(days=10),
            status=RequestStatus.OPEN,
        )

        response = client.get(reverse("purchase_requests:list"))
        assert response.status_code == 200
        assert "Recherche Lot Rame Papier A4" in response.content.decode("utf-8")

        response = client.get(reverse("purchase_requests:detail", kwargs={"pk": req.pk}))
        assert response.status_code == 200
        assert "50 cartons" in response.content.decode("utf-8")

    def test_join_purchase_request_flow(self, client, buyer_user, category, country):
        req = PurchaseRequest.objects.create(
            creator=buyer_user,
            category=category,
            country=country,
            title="Groupe d'achat Ecouteurs TWS",
            description="Recherche 20 paires d'écouteurs Bluetooth",
            target_price=Decimal("12000"),
            target_quantity=20,
            expires_at=timezone.now() + timezone.timedelta(days=7),
            status=RequestStatus.OPEN,
        )

        joiner = User.objects.create_user(
            phone="+22997000009",
            email="joiner@test.app",
            password="Password123!",
            role=UserRole.BUYER,
        )
        client.force_login(joiner)

        # GET join page
        get_resp = client.get(reverse("purchase_requests:join", kwargs={"pk": req.pk}))
        assert get_resp.status_code == 200

        # POST join
        post_resp = client.post(
            reverse("purchase_requests:join", kwargs={"pk": req.pk}),
            {"quantity_pledged": 3},
            follow=True,
        )
        assert post_resp.status_code == 200
        assert req.participants.filter(user=joiner).exists()
        participant = req.participants.get(user=joiner)
        assert participant.quantity_pledged == 3


@pytest.mark.django_db
class TestReviewsSystem:
    def test_create_review_on_paid_order(self, client, buyer_user, paid_order, product, store):
        client.force_login(buyer_user)

        # GET review form
        resp = client.get(reverse("reviews:create", kwargs={"order_number": paid_order.order_number}))
        assert resp.status_code == 200
        assert "Avis" in resp.content.decode("utf-8")

        # POST valid review
        post_resp = client.post(
            reverse("reviews:create", kwargs={"order_number": paid_order.order_number}),
            {
                "rating": 5,
                "comment": "Produit absolument fantastique et conforme !",
            },
            follow=True,
        )
        assert post_resp.status_code == 200
        assert Review.objects.filter(order=paid_order).exists()
        review = Review.objects.get(order=paid_order)
        assert review.rating == 5
        assert review.is_verified_purchase is True
        assert review.store == store
        assert review.product == product

    def test_cannot_review_twice(self, client, buyer_user, paid_order, product, store):
        client.force_login(buyer_user)
        Review.objects.create(
            order=paid_order,
            product=product,
            store=store,
            author=buyer_user,
            rating=4,
            comment="Déjà noté",
        )

        # Second attempt redirects with message
        resp = client.get(reverse("reviews:create", kwargs={"order_number": paid_order.order_number}), follow=True)
        assert resp.status_code == 200
        assert "Vous avez déjà déposé un avis" in resp.content.decode("utf-8")


@pytest.mark.django_db
class TestDisputesSystem:
    def test_open_dispute_and_send_message(self, client, buyer_user, paid_order):
        client.force_login(buyer_user)

        # GET dispute form
        get_resp = client.get(reverse("disputes:create", kwargs={"order_number": paid_order.order_number}))
        assert get_resp.status_code == 200
        assert "Ouvrir une Réclamation" in get_resp.content.decode("utf-8")

        # POST open dispute
        post_resp = client.post(
            reverse("disputes:create", kwargs={"order_number": paid_order.order_number}),
            {
                "reason": "Produit endommagé ou cassé au déballage",
                "description": "L'emballage était écrasé et l'article présente des rayures.",
            },
            follow=True,
        )
        assert post_resp.status_code == 200
        assert Dispute.objects.filter(order=paid_order).exists()
        dispute = Dispute.objects.get(order=paid_order)
        assert dispute.status == DisputeStatus.OPEN

        # Send a message in dispute
        msg_resp = client.post(
            reverse("disputes:detail", kwargs={"pk": dispute.pk}),
            {"message": "Voici des détails supplémentaires pour le médiateur."},
            follow=True,
        )
        assert msg_resp.status_code == 200
        assert dispute.messages.filter(sender=buyer_user).exists()
        msg = dispute.messages.first()
        assert "détails supplémentaires" in msg.message


@pytest.mark.django_db
class TestNotificationsSystem:
    def test_notification_flow(self, client, buyer_user):
        notif = Notification.objects.create(
            recipient=buyer_user,
            title="Palier Débloqué !",
            message="Le palier 3 de votre campagne vient d'être atteint.",
            link="/dashboard/campaigns/",
            is_read=False,
        )

        client.force_login(buyer_user)
        list_resp = client.get(reverse("notifications:list"))
        assert list_resp.status_code == 200
        assert "Palier Débloqué !" in list_resp.content.decode("utf-8")

        # Mark as read
        read_resp = client.get(reverse("notifications:mark_read", kwargs={"notification_id": notif.id}))
        assert read_resp.status_code == 302
        notif.refresh_from_db()
        assert notif.is_read is True
