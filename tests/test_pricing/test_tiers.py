from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from apps.pricing.validators import validate_price_tiers


def test_validate_valid_tiers():
    tiers = [
        {"min_participants": 2, "max_participants": 5, "price": "18000"},
        {"min_participants": 6, "max_participants": 10, "price": "16000"},
        {"min_participants": 11, "max_participants": None, "price": "14000"},
    ]
    # original = 20000, min = 12000
    assert validate_price_tiers(tiers, minimum_price=Decimal("12000"), original_price=Decimal("20000")) is True


def test_validate_rejects_price_below_minimum():
    tiers = [
        {"min_participants": 2, "max_participants": 5, "price": "11000"},  # below 12000!
    ]
    with pytest.raises(ValidationError, match="descend sous le prix minimum"):
        validate_price_tiers(tiers, minimum_price=Decimal("12000"), original_price=Decimal("20000"))


def test_validate_rejects_non_decreasing_prices():
    tiers = [
        {"min_participants": 2, "max_participants": 5, "price": "15000"},
        {"min_participants": 6, "max_participants": 10, "price": "16000"},  # more expensive!
    ]
    with pytest.raises(ValidationError, match="Dégressivité non respectée"):
        validate_price_tiers(tiers, minimum_price=Decimal("10000"), original_price=Decimal("20000"))


def test_validate_rejects_gap_between_tiers():
    tiers = [
        {"min_participants": 2, "max_participants": 5, "price": "16000"},
        {"min_participants": 8, "max_participants": 12, "price": "14000"},  # gap between 5 and 8!
    ]
    with pytest.raises(ValidationError, match="Incohérence entre les paliers"):
        validate_price_tiers(tiers, minimum_price=Decimal("10000"), original_price=Decimal("20000"))
