from django.shortcuts import redirect
from .models import Country


def change_country(request):
    """
    Permet à l'utilisateur de changer dynamiquement son pays et sa monnaie active.
    Stocke le choix en session et en cookie persistant.
    """
    country_code = request.GET.get("country") or request.POST.get("country")
    next_url = (
        request.GET.get("next")
        or request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or "/"
    )

    if country_code:
        country_code = country_code.strip().upper()
        if Country.objects.filter(code=country_code, is_active=True).exists():
            request.session["country_code"] = country_code
            response = redirect(next_url)
            response.set_cookie("country_code", country_code, max_age=365 * 24 * 60 * 60)
            return response

    return redirect(next_url)
