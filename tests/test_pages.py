import pytest
from django.test import Client
from apps.countries.models import Country, Currency


@pytest.fixture
def country(db):
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "FCFA"})
    return Country.objects.create(
        code="BJ",
        name="Bénin",
        phone_prefix="+229",
        flag_emoji="🇧🇯",
        currency=currency,
        is_active=True,
    )


@pytest.mark.django_db
def test_pages_availability(client: Client, country):
    # Accueil
    resp = client.get("/")
    assert resp.status_code == 200
    assert "REDUX" in resp.content.decode()

    # Explorer
    resp = client.get("/explorer/")
    assert resp.status_code == 200
    assert "Explorer les Achats Groupés" in resp.content.decode()

    # Comment ça marche
    resp = client.get("/comment-ca-marche/")
    assert resp.status_code == 200

    # Centre d'aide
    resp = client.get("/aide/")
    assert resp.status_code == 200

    # CGU
    resp = client.get("/cgu/")
    assert resp.status_code == 200

    # Confidentialité
    resp = client.get("/confidentialite/")
    assert resp.status_code == 200

    # PWA Offline
    resp = client.get("/offline/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_seo_robots_and_sitemap(client: Client):
    # Robots.txt
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/plain")
    content = resp.content.decode()
    assert "Disallow: /admin/" in content
    assert "Sitemap:" in content

    # Sitemap.xml
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "xml" in resp["Content-Type"]
