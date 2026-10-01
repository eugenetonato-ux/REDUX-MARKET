from decimal import Decimal
import json
import pytest
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.countries.models import Country, Currency
from apps.orders.models import Order, OrderStatus
from apps.payments.models import Payment, PaymentStatus
from apps.payments.providers.mock import MockPaymentProvider
from apps.payments.services import handle_webhook, initiate_payment


@pytest.fixture
def payment_fixture():
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "CFA"})
    country, _ = Country.objects.get_or_create(code="BJ", defaults={"name": "Bénin", "phone_prefix": "+229", "currency": currency})
    buyer = User.objects.create_user(email="buyer_pay@redux.app", password="password123", role=UserRole.BUYER)

    order = Order.objects.create(
        order_number="RDX-202609-PAY001",
        buyer=buyer,
        currency=currency,
        total_amount=Decimal("35000.00"),
        final_amount=Decimal("35000.00"),
        status=OrderStatus.PENDING,
        shipping_address="Cotonou",
        contact_phone="+22997000001",
    )

    payment, url = initiate_payment(order=order, provider_code="mock", user=buyer)
    return {
        "order": order,
        "payment": payment,
        "provider": MockPaymentProvider(),
    }


@pytest.mark.django_db
def test_webhook_invalid_signature_rejected(payment_fixture):
    payload = b'{"event_id": "EVT-1", "data": {}}'
    bad_signature = "bad_signature_hash"

    ok, msg, status = handle_webhook("mock", payload, bad_signature)
    assert ok is False
    assert status == 401
    assert "invalide" in msg


@pytest.mark.django_db
def test_webhook_successful_confirmation_validates_order(payment_fixture):
    order = payment_fixture["order"]
    payment = payment_fixture["payment"]
    prov = payment_fixture["provider"]

    assert order.status == OrderStatus.PENDING
    assert payment.status == PaymentStatus.PENDING

    payload_dict = {
        "event_id": "EVT-MOCK-SUCCESS-001",
        "event_type": "payment.succeeded",
        "data": {
            "reference": payment.reference,
            "status": "SUCCESS",
            "amount": "35000.00",
            "currency": "XOF",
        },
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    sig = prov.generate_test_signature(payload_bytes)

    ok, msg, status = handle_webhook("mock", payload_bytes, sig)
    assert ok is True
    assert status == 200

    order.refresh_from_db()
    payment.refresh_from_db()

    assert payment.status == PaymentStatus.SUCCESS
    assert order.status == OrderStatus.PAID


@pytest.mark.django_db
def test_webhook_amount_mismatch_rejected(payment_fixture):
    payment = payment_fixture["payment"]
    prov = payment_fixture["provider"]

    # Attendu: 35000 XOF. Le webhook envoie 10000 XOF !
    payload_dict = {
        "event_id": "EVT-MOCK-TAMPERED-001",
        "event_type": "payment.succeeded",
        "data": {
            "reference": payment.reference,
            "status": "SUCCESS",
            "amount": "10000.00",  # écart frauduleux !
            "currency": "XOF",
        },
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    sig = prov.generate_test_signature(payload_bytes)

    ok, msg, status = handle_webhook("mock", payload_bytes, sig)
    assert ok is False
    assert status == 400
    assert "Incohérence" in msg
