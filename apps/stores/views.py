from django.shortcuts import get_object_or_404, render
from .models import Store
from .selectors import get_store_by_slug, list_active_stores


def store_list_view(request):
    country = getattr(request, "country", None)
    stores = list_active_stores(country=country)
    context = {
        "stores": stores,
        "current_country": country,
    }
    return render(request, "stores/store_list.html", context)


def store_detail_view(request, slug):
    store = get_object_or_404(Store.objects.select_related("merchant", "country"), slug=slug, is_active=True)
    products = store.products.filter(is_active=True).prefetch_related("images")
    active_campaigns = store.merchant.campaigns.filter(status="ACTIVE").select_related("product")

    context = {
        "store": store,
        "products": products,
        "active_campaigns": active_campaigns,
    }
    return render(request, "stores/store_detail.html", context)
