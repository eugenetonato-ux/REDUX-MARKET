import pytest
from django.urls import reverse
from apps.countries.models import Country, Currency


@pytest.mark.django_db
def test_country_change_view(client):
    currency_xof = Currency.objects.create(code="XOF", name="Franc CFA", symbol="CFA")
    currency_ghs = Currency.objects.create(code="GHS", name="Cedi", symbol="GH₵")
    Country.objects.create(code="BJ", name="Bénin", phone_prefix="+229", currency=currency_xof, is_active=True)
    Country.objects.create(code="GH", name="Ghana", phone_prefix="+233", currency=currency_ghs, is_active=True)

    url = reverse("countries:change")
    response = client.get(f"{url}?country=GH&next=/")
    assert response.status_code == 302
    assert response.url == "/"
    assert client.session.get("country_code") == "GH"
    assert response.cookies.get("country_code").value == "GH"


@pytest.mark.django_db
def test_country_context_processor(client):
    currency_xof = Currency.objects.create(code="XOF", name="Franc CFA", symbol="CFA")
    Country.objects.create(code="BJ", name="Bénin", phone_prefix="+229", currency=currency_xof, is_active=True)

    response = client.get("/")
    assert response.status_code == 200
    assert "available_countries" in response.context
    assert "current_country" in response.context
