from django.conf import settings
from django.shortcuts import redirect
from django.utils.translation import activate
from .models import Country

ENGLISH_SPEAKING_COUNTRIES = {"NG", "GH", "KE", "RW"}


def change_country(request):
    """
    Permet à l'utilisateur de changer dynamiquement son pays et sa monnaie active.
    Bascule automatiquement la langue en anglais (EN) pour le Nigeria, Ghana, Kenya, Rwanda,
    et en français (FR) pour les pays francophones.
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
            
            # Détection et bascule de langue automatique
            target_lang = "en" if country_code in ENGLISH_SPEAKING_COUNTRIES else "fr"
            request.session["django_language"] = target_lang
            activate(target_lang)

            response = redirect(next_url)
            response.set_cookie("country_code", country_code, max_age=365 * 24 * 60 * 60)
            cookie_name = getattr(settings, "LANGUAGE_COOKIE_NAME", "django_language")
            response.set_cookie(cookie_name, target_lang, max_age=365 * 24 * 60 * 60)
            return response

    return redirect(next_url)


