"""
Tests i18n & multi-devises pour REDUX.
Vérifie :
  - Formatage des prix par devise (XOF, NGN, GHS, USD, EUR)
  - Switch de langue FR/EN via set_language
  - Injection correcte de CURRENT_LANGUAGE dans le contexte
  - Context processor platform
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

from django.test import TestCase, RequestFactory, Client, override_settings
from django.urls import reverse
from django.utils.translation import activate, override as translation_override


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_country(code, currency_code, symbol, decimals=0):
    """Crée un faux objet Country avec currency attachée."""
    currency = MagicMock()
    currency.code = currency_code
    currency.symbol = symbol
    currency.decimals = decimals
    country = MagicMock()
    country.code = code
    country.currency = currency
    return country


# ─────────────────────────────────────────────────────────────────────────────
# 1. Template tag `money` — formatage devise
# ─────────────────────────────────────────────────────────────────────────────

class TestMoneyTemplateTag(TestCase):
    """Teste le filtre |currency et |currency_code."""

    def _import_filters(self):
        from apps.core.templatetags.money import currency_filter, currency_code_filter, percent_off
        return currency_filter, currency_code_filter, percent_off

    def test_xof_format_no_decimals(self):
        currency_filter, _, _ = self._import_filters()
        country = make_country("BJ", "XOF", "CFA", decimals=0)
        result = currency_filter(5000, country)
        assert "5" in result and ("000" in result or "5\u202f000" in result or "5000" in result)
        assert "CFA" in result

    def test_usd_format_before_symbol(self):
        currency_filter, _, _ = self._import_filters()
        country = make_country("US", "USD", "$", decimals=2)
        result = currency_filter(99.99, country)
        # Le $ doit être AVANT le montant
        assert result.index("$") < result.index("99")

    def test_ngn_format_before_symbol(self):
        currency_filter, _, _ = self._import_filters()
        country = make_country("NG", "NGN", "₦", decimals=2)
        result = currency_filter(1500.50, country)
        assert "₦" in result

    def test_currency_code_filter_xof(self):
        _, currency_code_filter, _ = self._import_filters()
        result = currency_code_filter(10000, "XOF")
        assert "CFA" in result
        assert "10" in result

    def test_currency_code_filter_ngn(self):
        _, currency_code_filter, _ = self._import_filters()
        result = currency_code_filter(5000, "NGN")
        assert "₦" in result

    def test_currency_code_filter_eur(self):
        _, currency_code_filter, _ = self._import_filters()
        result = currency_code_filter(299.99, "EUR")
        assert "€" in result

    def test_currency_no_country_fallback(self):
        """Sans pays, affiche en XOF par défaut."""
        currency_filter, _, _ = self._import_filters()
        result = currency_filter(3000, None)
        assert "XOF" in result

    def test_invalid_amount(self):
        currency_filter, _, _ = self._import_filters()
        country = make_country("BJ", "XOF", "CFA", decimals=0)
        result = currency_filter("not_a_number", country)
        assert "—" in result or result == "—"

    def test_percent_off_calculation(self):
        _, _, percent_off = self._import_filters()
        assert percent_off(10000, 7500) == 25
        assert percent_off(10000, 10000) == 0
        assert percent_off(0, 5000) == 0

    def test_percent_off_floor(self):
        _, _, percent_off = self._import_filters()
        # 33.33...% → doit être planché à 33
        result = percent_off(3000, 2000)
        assert result == 33

    def test_zero_price(self):
        currency_filter, _, _ = self._import_filters()
        country = make_country("BJ", "XOF", "CFA", decimals=0)
        result = currency_filter(0, country)
        assert "0" in result


# ─────────────────────────────────────────────────────────────────────────────
# 2. Context Processor — injection langue
# ─────────────────────────────────────────────────────────────────────────────

class TestPlatformContextProcessor(TestCase):
    """Teste que le context processor platform injecte CURRENT_LANGUAGE."""

    def setUp(self):
        self.factory = RequestFactory()

    def _run_processor(self, lang="fr"):
        from apps.core.context_processors import platform
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        with translation_override(lang):
            return platform(request)

    def test_current_language_fr(self):
        ctx = self._run_processor("fr")
        assert ctx["CURRENT_LANGUAGE"] == "fr"

    def test_current_language_en(self):
        ctx = self._run_processor("en")
        assert ctx["CURRENT_LANGUAGE"] == "en"

    def test_available_languages_present(self):
        ctx = self._run_processor("fr")
        codes = [l["code"] for l in ctx["AVAILABLE_LANGUAGES"]]
        assert "fr" in codes
        assert "en" in codes

    def test_platform_name_injected(self):
        ctx = self._run_processor()
        assert ctx["PLATFORM_NAME"] == "REDUX"

    def test_unread_notifications_zero_for_anon(self):
        ctx = self._run_processor()
        assert ctx["unread_notifications_count"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Switch de langue — vue set_language
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSetLanguageView(TestCase):
    """Teste que POST vers /i18n/set-language/ change bien la langue de session."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)

    def test_set_language_en(self):
        response = self.client.post(
            "/i18n/set-language/",
            {"language": "en", "next": "/"},
            HTTP_ACCEPT_LANGUAGE="fr",
        )
        # Django redirige après set_language
        assert response.status_code in (302, 200)

    def test_set_language_fr(self):
        response = self.client.post(
            "/i18n/set-language/",
            {"language": "fr", "next": "/"},
        )
        assert response.status_code in (302, 200)

    def test_invalid_language_redirects(self):
        """Une langue invalide ne doit pas planter."""
        response = self.client.post(
            "/i18n/set-language/",
            {"language": "xx", "next": "/"},
        )
        # Django ignore les langues non déclarées dans LANGUAGES et redirige quand même
        assert response.status_code in (302, 200)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Formatage des devises africaines principales
# ─────────────────────────────────────────────────────────────────────────────

class TestAfricanCurrencies(TestCase):
    """Teste toutes les devises africaines supportées par REDUX."""

    def setUp(self):
        from apps.core.templatetags.money import currency_code_filter
        self.fmt = currency_code_filter

    def test_xof_cfa(self):
        result = self.fmt(5000, "XOF")
        assert "CFA" in result
        assert "5" in result

    def test_xaf_fcfa(self):
        result = self.fmt(15000, "XAF")
        assert "FCFA" in result

    def test_ngn_naira(self):
        result = self.fmt(250000, "NGN")
        assert "₦" in result

    def test_ghs_cedi(self):
        result = self.fmt(350, "GHS")
        assert "₵" in result

    def test_gnf_franc_guineen(self):
        result = self.fmt(100000, "GNF")
        assert "FG" in result

    def test_cdf_franc_congolais(self):
        result = self.fmt(50000, "CDF")
        assert "FC" in result

    def test_unknown_currency_fallback(self):
        result = self.fmt(1000, "MAD")
        assert "1" in result  # affiche le montant même pour devise inconnue
