from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from apps.catalog.selectors import list_categories
from .models import Campaign, CampaignStatus
from .selectors import get_campaign_by_slug, get_campaign_summary, list_active_campaigns
from .services import join_campaign


def campaign_list_view(request):
    category_slug = request.GET.get("category")
    search = request.GET.get("q")
    country = getattr(request, "country", None)
    country_code = country.code if country else "ALL"

    from django.core.cache import cache

    # Cache categories (15 min)
    categories = cache.get("campaign_list_categories")
    if categories is None:
        categories = list(list_categories())
        cache.set("campaign_list_categories", categories, 900)

    # Only cache when no search query is active
    cache_key = f"campaign_list_{country_code}_{category_slug or 'all'}"
    campaign_cards = None if search else cache.get(cache_key)

    if campaign_cards is None:
        campaigns = list_active_campaigns(category_slug=category_slug, country=country, search=search)
        campaign_cards = []
        for camp in campaigns:
            campaign_cards.append({
                "campaign": camp,
                "summary": get_campaign_summary(camp),
            })
        if not search:
            cache.set(cache_key, campaign_cards, 60)

    context = {
        "campaign_cards": campaign_cards,
        "categories": categories,
        "current_category_slug": category_slug,
        "search_query": search,
    }
    return render(request, "campaigns/campaign_list.html", context)


def campaign_detail_view(request, slug):
    campaign = get_object_or_404(
        Campaign.objects.select_related(
            "product",
            "merchant",
            "creator",
            "product__store",
            "product__category",
            "product__store__country",
            "product__store__country__currency",
        ).prefetch_related("tiers", "product__images"),
        slug=slug,
    )

    # Si la campagne n'est pas publique et que l'utilisateur n'est ni le créateur ni admin
    if campaign.status in [CampaignStatus.DRAFT, CampaignStatus.PENDING_APPROVAL]:
        if not (request.user.is_authenticated and (request.user == campaign.creator or request.user.is_admin)):
            return render(request, "errors/404.html", status=404)

    summary = get_campaign_summary(campaign)
    tiers = list(campaign.tiers.all().order_by("min_participants"))

    # Vérifier si l'utilisateur connecté participe déjà
    user_participation = None
    if request.user.is_authenticated:
        user_participation = campaign.participants.filter(user=request.user, status="JOINED").first()

    context = {
        "campaign": campaign,
        "summary": summary,
        "tiers": tiers,
        "user_participation": user_participation,
    }
    return render(request, "campaigns/campaign_detail.html", context)


@login_required
def campaign_join_view(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)

    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
            if quantity < 1:
                quantity = 1
            participant = join_campaign(campaign=campaign, user=request.user, quantity=quantity)
            messages.success(
                request,
                f"Félicitations ! Vous avez rejoint la campagne '{campaign.title}' pour {quantity} unité(s)."
            )
            return redirect("orders:checkout", participant_id=participant.id)
        except ValidationError as e:

            messages.error(request, e.message if hasattr(e, "message") else str(e))
            return redirect("campaigns:detail", slug=slug)

    return redirect("campaigns:detail", slug=slug)
