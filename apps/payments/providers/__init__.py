from .base import BasePaymentProvider
from .mock import MockPaymentProvider
from .registry import registry

# Enregistrement des prestataires disponibles
mock_provider = MockPaymentProvider()
registry.register(mock_provider)

__all__ = ["registry", "BasePaymentProvider", "MockPaymentProvider"]
