from django.conf import settings


def platform(request):
    return {
        "PLATFORM_NAME": getattr(settings, "PLATFORM_NAME", "REDUX"),
        "DEFAULT_COUNTRY_CODE": getattr(settings, "DEFAULT_COUNTRY_CODE", "BJ"),
    }
