from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass
class PaymentInitializationResult:
    payment_url: str
    provider_reference: str
    raw_data: Dict[str, Any]


@dataclass
class ParsedWebhookEvent:
    event_id: str
    event_type: str
    reference: str
    status: str  # 'SUCCESS', 'FAILED', 'PENDING'
    amount: Decimal
    currency: str
    raw_payload: Dict[str, Any]


class BasePaymentProvider(ABC):
    code: str = ""
    name: str = ""

    @abstractmethod
    def initialize_payment(self, payment, return_url: str, cancel_url: str) -> PaymentInitializationResult:
        """Initialise la session auprès du prestataire de paiement."""
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        """Vérifie la signature cryptographique du webhook pour s'assurer de sa provenance authentique."""
        pass

    @abstractmethod
    def parse_webhook_event(self, payload_dict: Dict[str, Any]) -> ParsedWebhookEvent:
        """Extrait et normalise les données de l'événement webhook."""
        pass
