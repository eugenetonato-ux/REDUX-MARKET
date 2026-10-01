from typing import Dict, Type
from .base import BasePaymentProvider


class PaymentProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, BasePaymentProvider] = {}

    def register(self, provider_instance: BasePaymentProvider):
        self._providers[provider_instance.code] = provider_instance

    def get_provider(self, code: str) -> BasePaymentProvider:
        if code not in self._providers:
            raise ValueError(f"Fournisseur de paiement inconnu ou non enregistré : '{code}'.")
        return self._providers[code]

    def list_providers(self) -> Dict[str, str]:
        return {code: p.name for code, p in self._providers.items()}


registry = PaymentProviderRegistry()
