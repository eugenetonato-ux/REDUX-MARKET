from .models import Country


def country(request):
    """
    Injecte le pays actif et la liste de tous les pays africains configurés
    dans le contexte de rendu de tous les templates Django.
    """
    return {
        "current_country": getattr(request, "country", None),
        "available_countries": Country.objects.filter(is_active=True).select_related("currency").order_by("name"),
    }
