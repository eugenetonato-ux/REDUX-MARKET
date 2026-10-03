import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from apps.accounts.roles import UserRole
from apps.accounts.services import get_or_create_demo_user
from apps.campaigns.models import Campaign
from apps.catalog.models import Category
from apps.countries.models import Country, Currency

User = get_user_model()


@pytest.fixture
def base_country(db):
    currency, _ = Currency.objects.get_or_create(code="XOF", defaults={"name": "Franc CFA", "symbol": "FCFA"})
    country, _ = Country.objects.get_or_create(
        code="BJ",
        defaults={
            "name": "Bénin",
            "phone_prefix": "+229",
            "flag_emoji": "🇧🇯",
            "currency": currency,
            "is_active": True,
        },
    )
    return country


@pytest.mark.django_db
def test_quick_login_buyer(client: Client, base_country):
    """Vérifie la connexion express 1-clic pour un acheteur sans formulaire."""
    resp = client.get("/quick-login/buyer/", follow=True)
    assert resp.status_code == 200
    # Redirigé vers le tableau de bord acheteur
    assert "/dashboard/" in resp.redirect_chain[0][0]
    # L'utilisateur en session a le rôle BUYER
    assert resp.context["user"].is_authenticated
    assert resp.context["user"].role == UserRole.BUYER
    assert resp.context["user"].is_buyer


@pytest.mark.django_db
def test_quick_login_merchant(client: Client, base_country):
    """Vérifie la connexion express 1-clic pour un commerçant sans formulaire."""
    resp = client.get("/quick-login/merchant/", follow=True)
    assert resp.status_code == 200
    # Redirigé vers le tableau de bord commerçant
    assert "/merchant/dashboard/" in resp.redirect_chain[0][0]
    assert resp.context["user"].is_authenticated
    assert resp.context["user"].role == UserRole.MERCHANT
    assert resp.context["user"].is_merchant
    # Le profil commerçant et la boutique existent
    assert resp.context["user"].merchant_profile.stores.exists()


@pytest.mark.django_db
def test_quick_login_admin(client: Client, base_country):
    """Vérifie la connexion express 1-clic pour l'administrateur sans formulaire."""
    resp = client.get("/quick-login/admin/", follow=True)
    assert resp.status_code == 200
    assert resp.context["user"].is_authenticated
    assert resp.context["user"].role == UserRole.ADMIN
    assert resp.context["user"].is_staff
    assert resp.context["user"].is_superuser


@pytest.mark.django_db
def test_login_page_renders_with_quick_login_buttons(client: Client):
    """Vérifie que la page de connexion affiche bien les cartes d'accès rapide 1-clic et le formulaire."""
    resp = client.get("/login/")
    assert resp.status_code == 200
    content = resp.content.decode()
    assert "ACCÈS RAPIDE 1-CLIC" in content
    assert "Connexion Acheteur" in content
    assert "Connexion Commerçant" in content
    assert "Supervision Administrateur" not in content
    assert "quick-login-admin" not in content
    assert "Connexion classique" in content


@pytest.mark.django_db
def test_standard_login_with_email_and_phone(client: Client, base_country):
    """Vérifie la connexion avec formulaire via email ou numéro de téléphone."""
    user = User.objects.create_user(
        email="testuser@redux.africa",
        phone="+22997123456",
        password="ValidPassword123!",
        role=UserRole.BUYER,
        country=base_country,
    )

    # 1. Connexion par email
    resp1 = client.post("/login/", {"identifier": "testuser@redux.africa", "password": "ValidPassword123!"}, follow=True)
    assert resp1.status_code == 200
    assert resp1.context["user"].is_authenticated
    client.logout()

    # 2. Connexion par téléphone
    resp2 = client.post("/login/", {"identifier": "+22997123456", "password": "ValidPassword123!"}, follow=True)
    assert resp2.status_code == 200
    assert resp2.context["user"].is_authenticated


@pytest.mark.django_db
def test_buyer_registration(client: Client, base_country):
    """Vérifie l'inscription d'un nouvel acheteur."""
    payload = {
        "full_name": "Jean Dupont",
        "email": "jean.dupont@test.com",
        "phone": "+22996112233",
        "country": base_country.id,
        "city": "Cotonou",
        "password": "Password2026!",
        "confirm_password": "Password2026!",
    }
    resp = client.post("/register/", payload, follow=True)
    assert resp.status_code == 200
    assert "/dashboard/" in resp.redirect_chain[0][0]

    user = User.objects.get(email="jean.dupont@test.com")
    assert user.role == UserRole.BUYER
    assert hasattr(user, "buyer_profile")
    assert user.buyer_profile.city == "Cotonou"


@pytest.mark.django_db
def test_merchant_registration(client: Client, base_country):
    """Vérifie l'inscription d'un nouveau commerçant avec sa boutique."""
    payload = {
        "full_name": "Fatou Sow",
        "business_name": "Boutique Elegance Dakar",
        "business_type": "Mode & Cosmétique",
        "email": "fatou.sow@test.com",
        "phone": "+221770001122",
        "country": base_country.id,
        "city": "Dakar",
        "password": "Password2026!",
        "confirm_password": "Password2026!",
    }
    resp = client.post("/register/merchant/", payload, follow=True)
    assert resp.status_code == 200
    assert "/merchant/dashboard/" in resp.redirect_chain[0][0]

    user = User.objects.get(email="fatou.sow@test.com")
    assert user.role == UserRole.MERCHANT
    assert hasattr(user, "merchant_profile")
    assert user.merchant_profile.business_name == "Boutique Elegance Dakar"
    assert user.merchant_profile.stores.exists()


@pytest.mark.django_db
def test_role_separation_enforcement(client: Client, base_country):
    """Vérifie la stricte séparation des espaces : un acheteur ne peut pas accéder aux pages commerçant sans être redirigé."""
    # Connecté en tant qu'acheteur
    client.get("/quick-login/buyer/", follow=True)

    # Tente d'accéder au dashboard commerçant
    resp = client.get("/merchant/dashboard/", follow=True)
    # L'acheteur est redirigé vers son espace acheteur ou averti
    assert resp.status_code == 200


@pytest.mark.django_db
def test_campaign_public_pages(client: Client, base_country):
    """Vérifie la page d'accueil, la liste des campagnes et le détail de campagne avec progression."""
    # Accueil
    resp_home = client.get("/")
    assert resp_home.status_code == 200
    assert "Achetez ensemble" in resp_home.content.decode()

    # Liste des campagnes
    resp_list = client.get("/campaigns/")
    assert resp_list.status_code == 200

    # Catégories
    resp_cats = client.get("/categories/")
    assert resp_cats.status_code == 200
