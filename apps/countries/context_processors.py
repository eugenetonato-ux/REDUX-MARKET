from .middleware import get_cached_countries_map
from .models import Country


def country(request):
    """
    Injecte le pays actif et la liste de tous les pays africains configurés
    dans le contexte de rendu de tous les templates Django depuis la mémoire RAM (0 ms).
    """
    countries_map = get_cached_countries_map()
    return {
        "current_country": getattr(request, "country", None),
        "available_countries": list(countries_map.values()),
    }
