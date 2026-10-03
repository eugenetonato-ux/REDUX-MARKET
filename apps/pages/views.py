from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render
from apps.campaigns.models import Campaign, CampaignStatus
from apps.campaigns.selectors import get_campaign_summary, list_active_campaigns
from apps.catalog.models import Category
from apps.countries.models import Country
from apps.merchants.models import VerificationStatus
from apps.purchase_requests.selectors import get_active_purchase_requests
from apps.stores.models import Store


from django.core.cache import cache


def home(request):
    current_country = getattr(request, "country", None)
    country_code = current_country.code if current_country else "ALL"

    # Cache des cartes de campagnes actives (60 secondes)
    cache_key_cards = f"home_campaign_cards_{country_code}"
    campaign_cards = cache.get(cache_key_cards)
    if campaign_cards is None:
        campaigns_qs = list_active_campaigns(country=current_country)[:6]
        campaign_cards = []
        for c in campaigns_qs:
            campaign_cards.append({
                "campaign": c,
                "summary": get_campaign_summary(c),
            })
        cache.set(cache_key_cards, campaign_cards, 60)

    # Cache des catégories racines (15 minutes)
    categories = cache.get("home_root_categories")
    if categories is None:
        categories = list(
            Category.objects.filter(is_active=True, parent__isnull=True).annotate(
                products_count=Count("products", filter=Q(products__is_active=True))
            )[:8]
        )
        cache.set("home_root_categories", categories, 900)

    return render(
        request,
        "pages/home.html",
        {
            "campaign_cards": campaign_cards,
            "categories": categories,
            "current_country": current_country,
        },
    )


def explorer(request):
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    country_code = request.GET.get("country", "").strip()
    item_type = request.GET.get("type", "all")  # 'all', 'campaigns', 'requests'

    country = None
    if country_code:
        country = Country.objects.filter(code=country_code.upper(), is_active=True).first()

    # Campagnes
    campaign_cards = []
    if item_type in ["all", "campaigns"]:
        campaigns_qs = list_active_campaigns(
            category_slug=category_slug if category_slug else None,
            country=country,
            search=query if query else None,
        )
        for c in campaigns_qs:
            campaign_cards.append({
                "campaign": c,
                "summary": get_campaign_summary(c),
            })

    # Demandes d'achat groupé
    purchase_requests = []
    if item_type in ["all", "requests"]:
        pr_qs = get_active_purchase_requests(country_code=country_code if country_code else None)
        if query:
            pr_qs = pr_qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
        purchase_requests = pr_qs

    categories = Category.objects.filter(is_active=True, parent__isnull=True)
    countries = Country.objects.filter(is_active=True)

    return render(
        request,
        "pages/explorer.html",
        {
            "query": query,
            "selected_category": category_slug,
            "selected_country": country_code,
            "selected_type": item_type,
            "campaign_cards": campaign_cards,
            "purchase_requests": purchase_requests,
            "categories": categories,
            "countries": countries,
        },
    )


def how_it_works(request):
    return render(request, "pages/how_it_works.html")


def help_view(request):
    return render(request, "pages/help.html")


def terms_view(request):
    return render(request, "pages/terms.html")


def privacy_view(request):
    return render(request, "pages/privacy.html")


def offline_view(request):
    return render(request, "pages/offline.html")


def categories_view(request):
    categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related("children").annotate(
        products_count=Count("products", filter=Q(products__is_active=True))
    )
    return render(request, "pages/categories.html", {"categories": categories})


def category_detail_view(request, slug):
    from django.shortcuts import get_object_or_404
    category = get_object_or_404(Category, slug=slug, is_active=True)
    campaigns_qs = list_active_campaigns(category_slug=slug)
    campaign_cards = []
    for c in campaigns_qs:
        campaign_cards.append({
            "campaign": c,
            "summary": get_campaign_summary(c),
        })
    return render(
        request,
        "pages/category_detail.html",
        {
            "category": category,
            "campaign_cards": campaign_cards,
        },
    )


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /dashboard/",
        "Disallow: /merchant/",
        "Disallow: /checkout/",
        "Disallow: /payments/",
        "Allow: /",
        f"Sitemap: https://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

