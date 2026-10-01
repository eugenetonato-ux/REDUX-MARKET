from decimal import Decimal
import pytest
from apps.pricing.calculators import (
    calculate_current_price,
    calculate_current_tier,
    calculate_savings,
    get_next_tier,
    get_remaining_participants,
)


class DummyTier:
    def __init__(self, id, min_p, max_p, price):
        self.id = id
        self.min_participants = min_p
        self.max_participants = max_p
        self.price = Decimal(str(price))


@pytest.fixture
def sample_tiers():
    return [
        DummyTier(1, 2, 5, "18000"),
        DummyTier(2, 6, 10, "15000"),
        DummyTier(3, 11, None, "12000"),
    ]


def test_calculate_tier_below_first(sample_tiers):
    # Only 1 participant: no tier reached yet
    tier = calculate_current_tier(sample_tiers, 1)
    assert tier is None
    price = calculate_current_price(sample_tiers, 1, fallback_price="20000")
    assert price == Decimal("20000")


def test_calculate_tier_in_middle(sample_tiers):
    # 4 participants -> tier 1
    tier = calculate_current_tier(sample_tiers, 4)
    assert tier.id == 1
    assert tier.price == Decimal("18000")

    # 7 participants -> tier 2
    tier = calculate_current_tier(sample_tiers, 7)
    assert tier.id == 2
    assert tier.price == Decimal("15000")


def test_calculate_tier_open_ended(sample_tiers):
    # 15 participants -> tier 3
    tier = calculate_current_tier(sample_tiers, 15)
    assert tier.id == 3
    assert tier.price == Decimal("12000")


def test_get_next_tier_and_remaining(sample_tiers):
    # At 4 participants, next tier is tier 2 (starts at 6)
    next_t = get_next_tier(sample_tiers, 4)
    assert next_t.id == 2
    assert get_remaining_participants(sample_tiers, 4) == 2

    # At 12 participants, already at highest tier
    assert get_next_tier(sample_tiers, 12) is None
    assert get_remaining_participants(sample_tiers, 12) == 0


def test_calculate_savings():
    saved_amount, saved_pct = calculate_savings("20000", "15000")
    assert saved_amount == Decimal("5000.00")
    assert saved_pct == Decimal("25.0")
