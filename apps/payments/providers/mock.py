from decimal import Decimal
import hashlib
import hmac
import json
from typing import Any, Dict
from django.conf import settings
from .base import BasePaymentProvider, ParsedWebhookEvent, PaymentInitializationResult


class MockPaymentProvider(BasePaymentProvider):
    code = "mock"
    name = "Simulateur Mobile Money / Carte (Mock)"

    def initialize_payment(self, payment, return_url: str, cancel_url: str) -> PaymentInitializationResult:
        ref = f"MOCK-{payment.idempotency_key}"
        # Direct URL to local success / pending simulation
        mock_url = f"/payment/pending/{payment.order.order_number}/"
        return PaymentInitializationResult(
            payment_url=mock_url,
            provider_reference=ref,
            raw_data={"status": "INITIALIZED", "reference": ref},
        )

    def generate_test_signature(self, payload_bytes: bytes) -> str:
        secret = getattr(settings, "PAYMENT_WEBHOOK_SECRET", "mock-secret-key-2026")
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        if not signature:
            return False
        expected = self.generate_test_signature(payload_bytes)
        return hmac.compare_digest(expected, signature)

    def parse_webhook_event(self, payload_dict: Dict[str, Any]) -> ParsedWebhookEvent:
        event_id = payload_dict.get("event_id", "")
        event_type = payload_dict.get("event_type", "payment.succeeded")
        data = payload_dict.get("data", {})

        return ParsedWebhookEvent(
            event_id=event_id,
            event_type=event_type,
            reference=data.get("reference", ""),
            status=data.get("status", "SUCCESS"),
            amount=Decimal(str(data.get("amount", "0"))),
            currency=data.get("currency", "XOF"),
            raw_payload=payload_dict,
        )
