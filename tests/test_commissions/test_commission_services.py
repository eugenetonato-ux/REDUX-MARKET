"""
Tests pour apps/commissions/ :
  - calculate_commission() : calcul pur
  - record_commission()    : enregistrement idempotent
  - _resolve_rule_safe()   : résolution de règle
  - estimate_commission()  : calculateur rapide
  - get_commissions_summary() : agrégats
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_mock_rule(rate=Decimal("5.00"), fixed_fee=Decimal("0.00")):
    rule = MagicMock()
    rule.rate_percentage = rate
    rule.fixed_fee = fixed_fee
    rule.pk = 1
    return rule


def make_mock_order(amount="10000.00", order_number="ORD-TEST-001"):
    order = MagicMock()
    order.final_amount = Decimal(amount)
    order.order_number = order_number
    order.campaign = None
    order.buyer = MagicMock()
    return order


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tests calculate_commission()
# ─────────────────────────────────────────────────────────────────────────────

class TestCalculateCommission(TestCase):

    def _calc(self, amount, rule=None):
        from apps.commissions.services import calculate_commission
        return calculate_commission(Decimal(str(amount)), rule)

    def test_default_rate_5_percent(self):
        result = self._calc(10000)
        self.assertEqual(result["rate_percentage"], Decimal("5.00"))
        self.assertEqual(result["commission_amount"], Decimal("500.00"))
        self.assertEqual(result["net_amount"], Decimal("9500.00"))

    def test_custom_rate(self):
        rule = make_mock_rule(rate=Decimal("10.00"), fixed_fee=Decimal("0.00"))
        result = self._calc(5000, rule)
        self.assertEqual(result["commission_amount"], Decimal("500.00"))
        self.assertEqual(result["net_amount"], Decimal("4500.00"))

    def test_fixed_fee_added(self):
        rule = make_mock_rule(rate=Decimal("5.00"), fixed_fee=Decimal("200.00"))
        result = self._calc(10000, rule)
        # 10000 * 5% + 200 = 700
        self.assertEqual(result["commission_amount"], Decimal("700.00"))
        self.assertEqual(result["net_amount"], Decimal("9300.00"))

    def test_commission_capped_at_gross(self):
        """La commission ne peut pas dépasser le montant brut."""
        rule = make_mock_rule(rate=Decimal("100.00"), fixed_fee=Decimal("999999.00"))
        result = self._calc(1000, rule)
        self.assertEqual(result["commission_amount"], Decimal("1000.00"))
        self.assertEqual(result["net_amount"], Decimal("0.00"))

    def test_zero_amount(self):
        result = self._calc(0)
        self.assertEqual(result["commission_amount"], Decimal("0.00"))
        self.assertEqual(result["net_amount"], Decimal("0.00"))

    def test_rounding_half_up(self):
        """5% de 100.01 = 5.0005 → arrondi à 5.00."""
        result = self._calc("100.01")
        self.assertEqual(result["commission_amount"], Decimal("5.00"))

    def test_fractional_rate(self):
        rule = make_mock_rule(rate=Decimal("2.50"), fixed_fee=Decimal("0.00"))
        result = self._calc(8000, rule)
        # 8000 * 2.5% = 200
        self.assertEqual(result["commission_amount"], Decimal("200.00"))
        self.assertEqual(result["net_amount"], Decimal("7800.00"))


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tests estimate_commission()
# ─────────────────────────────────────────────────────────────────────────────

class TestEstimateCommission(TestCase):

    def _estimate(self, amount, rate=Decimal("5.00"), fee=Decimal("0.00")):
        from apps.commissions.calculators import estimate_commission
        return estimate_commission(Decimal(str(amount)), rate, fee)

    def test_basic_estimate(self):
        result = self._estimate(20000)
        self.assertEqual(result["commission_amount"], Decimal("1000.00"))
        self.assertEqual(result["net_amount"], Decimal("19000.00"))

    def test_estimate_with_fee(self):
        result = self._estimate(10000, rate=Decimal("3.00"), fee=Decimal("100.00"))
        # 10000 * 3% + 100 = 400
        self.assertEqual(result["commission_amount"], Decimal("400.00"))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tests record_commission() — idempotence
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRecordCommission(TestCase):

    def _setup_db(self):
        """Crée les objets minimaux en base pour tester record_commission."""
        from apps.accounts.models import User
        from apps.countries.models import Currency, Country
        from apps.orders.models import Order

        currency, _ = Currency.objects.get_or_create(
            code="XOF", defaults={"name": "CFA", "symbol": "CFA", "decimals": 0}
        )
        country, _ = Country.objects.get_or_create(
            code="BJ",
            defaults={"name": "Benin", "phone_prefix": "+229", "currency": currency}
        )
        buyer, _ = User.objects.get_or_create(
            email="testbuyer@redux.app",
            defaults={"full_name": "Test Buyer", "is_active": True}
        )
        # Numéro unique par test pour éviter les conflits d'unicité
        import uuid
        order = Order.objects.create(
            order_number=f"ORD-COMM-{uuid.uuid4().hex[:8].upper()}",
            buyer=buyer,
            currency=currency,
            total_amount=Decimal("10000.00"),
            final_amount=Decimal("10000.00"),
            status="PAID",
            shipping_address="Cotonou, Benin",
            contact_phone="+22967000000",
        )
        return order

    def test_record_creates_platform_transaction(self):
        from apps.commissions.services import record_commission
        from apps.commissions.models import PlatformTransaction

        order = self._setup_db()
        pt = record_commission(order)

        self.assertIsNotNone(pt)
        self.assertIsInstance(pt, PlatformTransaction)
        self.assertEqual(pt.gross_amount, Decimal("10000.00"))
        self.assertEqual(pt.commission_amount, Decimal("500.00"))  # 5% par défaut
        self.assertEqual(pt.net_merchant_amount, Decimal("9500.00"))
        self.assertEqual(pt.status, "COMPLETED")

    def test_record_idempotent(self):
        """Deux appels successifs → toujours 1 seule PlatformTransaction."""
        from apps.commissions.services import record_commission
        from apps.commissions.models import PlatformTransaction

        order = self._setup_db()
        pt1 = record_commission(order)
        pt2 = record_commission(order)

        self.assertEqual(pt1.pk, pt2.pk)
        self.assertEqual(PlatformTransaction.objects.filter(order=order).count(), 1)

    def test_record_zero_amount_returns_none(self):
        from apps.commissions.services import record_commission

        order = self._setup_db()
        order.final_amount = Decimal("0.00")
        order.save()

        result = record_commission(order)
        self.assertIsNone(result)
