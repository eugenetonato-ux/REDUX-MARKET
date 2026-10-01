from django.db.models import Q
from .models import Category, Product


def list_active_products(category_slug=None, store_slug=None, search=None, is_featured=None):
    qs = Product.objects.filter(is_active=True).select_related("store", "category", "store__country", "store__country__currency").prefetch_related("images")

    if category_slug:
        qs = qs.filter(Q(category__slug=category_slug) | Q(category__parent__slug=category_slug))

    if store_slug:
        qs = qs.filter(store__slug=store_slug)

    if is_featured is not None:
        qs = qs.filter(is_featured=is_featured)

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search) | Q(store__name__icontains=search))

    return qs.order_by("-is_featured", "-created_at")


def get_product_by_slug(slug):
    return Product.objects.filter(slug=slug, is_active=True).select_related("store", "category", "store__country", "store__country__currency").prefetch_related("images", "variants").first()


def list_categories():
    return Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children")
