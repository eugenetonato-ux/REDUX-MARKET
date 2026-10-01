import pytest
from apps.payments.providers.base import BasePaymentProvider
from apps.payments.providers.registry import registry


class CustomTestProvider(BasePaymentProvider):
    code = "custom_test"
    name = "Custom Test Provider"

    def initialize_payment(self, payment, return_url: str, cancel_url: str):
        pass

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        return True

    def parse_webhook_event(self, payload_dict):
        pass


def test_provider_registration_and_retrieval():
    test_prov = CustomTestProvider()
    registry.register(test_prov)

    retrieved = registry.get_provider("custom_test")
    assert retrieved.code == "custom_test"
    assert retrieved.name == "Custom Test Provider"

    assert "mock" in registry.list_providers()
    assert "custom_test" in registry.list_providers()


def test_unknown_provider_raises_error():
    with pytest.raises(ValueError, match="Fournisseur de paiement inconnu"):
        registry.get_provider("non_existent_provider_xyz")
