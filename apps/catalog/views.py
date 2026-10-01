from django.shortcuts import get_object_or_404, render
from .models import Product
from .selectors import get_product_by_slug, list_active_products, list_categories


def product_list_view(request):
    category_slug = request.GET.get("category")
    search_query = request.GET.get("q")
    products = list_active_products(category_slug=category_slug, search=search_query)
    categories = list_categories()

    context = {
        "products": products,
        "categories": categories,
        "current_category_slug": category_slug,
        "search_query": search_query,
    }
    return render(request, "catalog/product_list.html", context)


def product_detail_view(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("store", "category", "store__country", "store__country__currency").prefetch_related("images", "variants"),
        slug=slug,
        is_active=True,
    )
    active_campaigns = product.campaigns.filter(status="ACTIVE").prefetch_related("tiers")

    context = {
        "product": product,
        "active_campaigns": active_campaigns,
    }
    return render(request, "catalog/product_detail.html", context)
