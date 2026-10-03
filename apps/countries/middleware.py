from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from .models import Country

CACHE_TTL_COUNTRIES = 3600  # 1 hour


def get_cached_countries_map():
    """
    Retourne la table de hachage de tous les pays actifs en mémoire (0 ms).
    Évite une requête SQL à chaque chargement de page.
    """
    countries_map = cache.get("all_active_countries_map")
    if countries_map is None:
        try:
            qs = list(Country.objects.filter(is_active=True).select_related("currency").order_by("name"))
            countries_map = {c.code: c for c in qs}
            cache.set("all_active_countries_map", countries_map, CACHE_TTL_COUNTRIES)
        except Exception:
            countries_map = {}
    return countries_map


class CountryMiddleware(MiddlewareMixin):
    def process_request(self, request):
        country_code = request.session.get("country_code") or request.COOKIES.get("country_code")
        if not country_code:
            country_code = getattr(settings, "DEFAULT_COUNTRY_CODE", "BJ")

        countries_map = get_cached_countries_map()
        country = countries_map.get(country_code)
        if not country and countries_map:
            country = next(iter(countries_map.values()), None)

        request.country = country
