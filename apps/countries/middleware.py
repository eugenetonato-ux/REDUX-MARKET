from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from .models import Country


class CountryMiddleware(MiddlewareMixin):
    def process_request(self, request):
        country_code = request.session.get("country_code") or request.COOKIES.get("country_code")
        if not country_code:
            country_code = getattr(settings, "DEFAULT_COUNTRY_CODE", "BJ")

        country = None
        try:
            country = Country.objects.select_related("currency").filter(code=country_code, is_active=True).first()
            if not country:
                country = Country.objects.select_related("currency").filter(is_active=True).first()
        except Exception:
            country = None

        request.country = country
