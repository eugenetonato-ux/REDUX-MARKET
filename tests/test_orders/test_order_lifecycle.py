from decimal import Decimal
import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.countries.models import Country, Currency
from apps.orders.models import Order, OrderStatus
from apps.orders.selectors import get_order_by_number
from apps.orders.state_machine import transition_order_status


@pytest.fixture
def base_order():
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "CFA"})
    country, _ = Country.objects.get_or_create(code="BJ", defaults={"name": "Bénin", "phone_prefix": "+229", "currency": currency})
    buyer = User.objects.create_user(email="lifecycle_buyer@redux.app", password="password123", role=UserRole.BUYER)

    order = Order.objects.create(
        order_number="RDX-202609-TEST01",
        buyer=buyer,
        currency=currency,
        total_amount=Decimal("50000.00"),
        final_amount=Decimal("50000.00"),
        status=OrderStatus.PENDING,
        shipping_address="Cotonou",
        contact_phone="+22997123456",
    )
    return {"order": order, "buyer": buyer}


@pytest.mark.django_db
def test_order_status_transitions(base_order):
    order = base_order["order"]
    buyer = base_order["buyer"]

    assert order.status == OrderStatus.PENDING

    # Transition to PAID
    transition_order_status(order, OrderStatus.PAID, actor=buyer, notes="Paiement mobile money reçu")
    order.refresh_from_db()
    assert order.status == OrderStatus.PAID
    assert order.status_history.count() == 1
    assert order.status_history.first().new_status == OrderStatus.PAID

    # Transition to PROCESSING
    transition_order_status(order, OrderStatus.PROCESSING)
    order.refresh_from_db()
    assert order.status == OrderStatus.PROCESSING

    # Transition to SHIPPED
    transition_order_status(order, OrderStatus.SHIPPED)
    order.refresh_from_db()
    assert order.status == OrderStatus.SHIPPED

    # Transition to DELIVERED
    transition_order_status(order, OrderStatus.DELIVERED)
    order.refresh_from_db()
    assert order.status == OrderStatus.DELIVERED


@pytest.mark.django_db
def test_order_invalid_status_jump(base_order):
    order = base_order["order"]

    # PENDING cannot jump directly to DELIVERED
    with pytest.raises(ValidationError, match="Transition de commande invalide"):
        transition_order_status(order, OrderStatus.DELIVERED)


@pytest.mark.django_db
def test_order_idor_access_control(base_order):
    order = base_order["order"]
    buyer = base_order["buyer"]
    third_party = User.objects.create_user(email="third_party@redux.app", password="password123", role=UserRole.BUYER)

    # Buyer can view their own order
    fetched = get_order_by_number(order.order_number, user=buyer)
    assert fetched.id == order.id

    # Third party user is rejected with PermissionDenied (anti-IDOR)
    with pytest.raises(PermissionDenied):
        get_order_by_number(order.order_number, user=third_party)
