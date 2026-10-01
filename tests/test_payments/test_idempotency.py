from decimal import Decimal
import json
import pytest
from apps.accounts.models import User
from apps.accounts.roles import UserRole
from apps.countries.models import Country, Currency
from apps.orders.models import Order, OrderStatus
from apps.payments.models import WebhookEvent
from apps.payments.providers.mock import MockPaymentProvider
from apps.payments.services import handle_webhook, initiate_payment


@pytest.mark.django_db
def test_webhook_idempotency_prevents_duplicate_processing():
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "CFA"})
    country, _ = Country.objects.get_or_create(code="BJ", defaults={"name": "Bénin", "phone_prefix": "+229", "currency": currency})
    buyer = User.objects.create_user(email="idempotent_buyer@redux.app", password="password123", role=UserRole.BUYER)

    order = Order.objects.create(
        order_number="RDX-202609-IDEM01",
        buyer=buyer,
        currency=currency,
        total_amount=Decimal("20000.00"),
        final_amount=Decimal("20000.00"),
        status=OrderStatus.PENDING,
        shipping_address="Cotonou",
        contact_phone="+22997000002",
    )

    payment, _ = initiate_payment(order=order, provider_code="mock", user=buyer)
    prov = MockPaymentProvider()

    payload_dict = {
        "event_id": "EVT-UNIQUE-IDEM-001",
        "event_type": "payment.succeeded",
        "data": {
            "reference": payment.reference,
            "status": "SUCCESS",
            "amount": "20000.00",
            "currency": "XOF",
        },
    }
    payload_bytes = json.dumps(payload_dict).encode("utf-8")
    sig = prov.generate_test_signature(payload_bytes)

    # 1ère réception : traité avec succès
    ok1, msg1, code1 = handle_webhook("mock", payload_bytes, sig)
    assert ok1 is True
    assert code1 == 200

    assert WebhookEvent.objects.filter(event_id="EVT-UNIQUE-IDEM-001").count() == 1
    event = WebhookEvent.objects.get(event_id="EVT-UNIQUE-IDEM-001")
    assert event.processed is True

    # 2ème réception du MÊME webhook (rejeu ou retry réseau du prestataire)
    ok2, msg2, code2 = handle_webhook("mock", payload_bytes, sig)
    assert ok2 is True
    assert code2 == 200
    assert "Idempotence" in msg2

    # Aucune duplication en base
    assert WebhookEvent.objects.filter(event_id="EVT-UNIQUE-IDEM-001").count() == 1
