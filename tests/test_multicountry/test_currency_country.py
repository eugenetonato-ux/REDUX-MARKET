import pytest
from apps.countries.models import Country, Currency


@pytest.mark.django_db
def test_country_currency_relation():
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "CFA"})
    country, _ = Country.objects.get_or_create(code="BJ", defaults={"name": "Bénin", "phone_prefix": "+229", "currency": currency})
    assert country.currency.code == "XOF"
    assert str(country) == "Bénin (BJ)"
