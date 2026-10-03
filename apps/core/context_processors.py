from django.conf import settings
from django.utils.translation import get_language


def platform(request):
    current_lang = get_language() or settings.LANGUAGE_CODE or "fr"
    # Normalise : "fr-fr" → "fr", "en-us" → "en"
    current_lang = current_lang.split("-")[0].lower()

    # Liste des langues disponibles enrichie
    available_languages = [
        {"code": "fr", "label": "Français", "flag": "🇫🇷"},
        {"code": "en", "label": "English", "flag": "🇬🇧"},
    ]

    ctx = {
        "PLATFORM_NAME": getattr(settings, "PLATFORM_NAME", "REDUX"),
        "DEFAULT_COUNTRY_CODE": getattr(settings, "DEFAULT_COUNTRY_CODE", "BJ"),
        "unread_notifications_count": 0,
        "CURRENT_LANGUAGE": current_lang,
        "AVAILABLE_LANGUAGES": available_languages,
    }
    if request.user.is_authenticated:
        try:
            ctx["unread_notifications_count"] = request.user.notifications.filter(is_read=False).count()
        except Exception:
            pass
    return ctx
