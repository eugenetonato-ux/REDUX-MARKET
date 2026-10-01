from .models import Store


def list_active_stores(country=None):
    qs = Store.objects.filter(is_active=True).select_related("merchant", "country")
    if country:
        qs = qs.filter(country=country)
    return qs.order_by("-rating_average", "-created_at")


def get_store_by_slug(slug):
    return Store.objects.filter(slug=slug, is_active=True).select_related("merchant", "country").first()
