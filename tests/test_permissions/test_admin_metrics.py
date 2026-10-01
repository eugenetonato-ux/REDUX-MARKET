from decimal import Decimal
import pytest
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.core.admin_dashboard import get_platform_metrics
from apps.countries.models import Country, Currency
from apps.merchants.models import MerchantProfile, VerificationStatus
from apps.merchants.services import create_merchant_profile
from apps.notifications.dispatcher import send_notification
from apps.notifications.models import NotificationPreference
from apps.orders.models import Order, OrderStatus
from apps.stores.services import create_store


@pytest.mark.django_db
def test_platform_metrics_aggregation():
    buyer = User.objects.create_user(email="buyer_metric@redux.app", password="password123", role=UserRole.BUYER)
    seller = User.objects.create_user(email="seller_metric@redux.app", password="password123", role=UserRole.MERCHANT)

    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "CFA"})
    country, _ = Country.objects.get_or_create(code="BJ", defaults={"name": "Bénin", "phone_prefix": "+229", "currency": currency})

    merchant = create_merchant_profile(seller, "Metric Store SARL")
    create_store(merchant, country, "Metric Store Cotonou")

    # Créer une commande payée
    Order.objects.create(
        order_number="RDX-202609-METRIC1",
        buyer=buyer,
        currency=currency,
        total_amount=Decimal("45000.00"),
        final_amount=Decimal("45000.00"),
        status=OrderStatus.PAID,
        shipping_address="Cotonou",
        contact_phone="+22997000099",
    )

    metrics = get_platform_metrics()
    assert metrics["total_buyers"] >= 1
    assert metrics["total_merchants"] >= 1
    assert metrics["paid_orders"] >= 1
    assert metrics["total_gmv"] >= Decimal("45000.00")


@pytest.mark.django_db
def test_notification_dispatcher_and_sanitization():
    user = User.objects.create_user(email="notif_user@redux.app", password="password123", role=UserRole.BUYER)

    # Test avec tentative d'injection script
    malicious_title = "<script>alert('XSS')</script>Nouveau palier"
    malicious_body = "<img src=x onerror=alert(1)>Votre groupe avance"

    notif = send_notification(recipient=user, title=malicious_title, message=malicious_body)

    assert notif is not None
    assert "<script>" not in notif.title
    assert "&lt;script&gt;" in notif.title
    assert notif.is_read is False


@pytest.mark.django_db
def test_notification_respects_opt_out():
    user = User.objects.create_user(email="quiet_user@redux.app", password="password123", role=UserRole.BUYER)
    pref, _ = NotificationPreference.objects.get_or_create(user=user)
    pref.in_app_notifications = False
    pref.save()

    notif = send_notification(recipient=user, title="Hello", message="World")
    assert notif is None
    assert user.notifications.count() == 0
