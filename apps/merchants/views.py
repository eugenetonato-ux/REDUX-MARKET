from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.decorators import merchant_required
from apps.campaigns.models import Campaign, CampaignStatus
from apps.campaigns.selectors import get_campaign_summary
from apps.catalog.models import Product
from apps.orders.models import Order, OrderStatus, OrderStatusHistory
from apps.orders.state_machine import transition_order_status
from apps.pricing.models import PriceTier

from .forms import CampaignCreateForm, OrderStatusUpdateForm, ProductForm, StoreForm
from .models import VerificationStatus
from .selectors import get_merchant_by_user, get_merchant_stats
from .services import create_merchant_profile, submit_verification_document


@login_required
@merchant_required
def dashboard_view(request):
    """Tableau de bord commerçant : KPIs de chiffre d'affaires, campagnes et commandes."""
    merchant = get_merchant_by_user(request.user)
    if not merchant:
        merchant = create_merchant_profile(
            user=request.user,
            business_name=f"Boutique de {request.user.full_name or request.user.email}",
        )

    stats = get_merchant_stats(merchant)
    stores = merchant.stores.all()
    primary_store = stores.first()

    # Campagnes récentes
    recent_campaigns = (
        Campaign.objects.filter(merchant=merchant)
        .select_related("product")
        .prefetch_related("tiers")
        .order_by("-created_at")[:4]
    )
    campaign_cards = []
    for c in recent_campaigns:
        campaign_cards.append({
            "campaign": c,
            "summary": get_campaign_summary(c),
        })

    # Commandes récentes
    recent_orders = (
        Order.objects.filter(campaign__merchant=merchant)
        .select_related("buyer", "campaign", "currency")
        .order_by("-created_at")[:6]
    )

    context = {
        "merchant": merchant,
        "primary_store": primary_store,
        "stores": stores,
        "stats": stats,
        "campaign_cards": campaign_cards,
        "recent_orders": recent_orders,
    }
    return render(request, "merchant/dashboard.html", context)


@login_required
@merchant_required
def products_list_view(request):
    """Catalogue des produits du commerçant."""
    merchant = get_merchant_by_user(request.user)
    products = Product.objects.filter(store__merchant=merchant).select_related("category", "store").order_by("-created_at")
    return render(request, "merchant/products.html", {"merchant": merchant, "products": products})


@login_required
@merchant_required
def product_create_view(request):
    """Ajout d'un nouveau produit par le commerçant."""
    merchant = get_merchant_by_user(request.user)
    primary_store = merchant.stores.first()

    if not primary_store:
        messages.error(request, "Veuillez d'abord configurer votre boutique.")
        return redirect("merchants:store")

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = primary_store

            # Génération d'un slug unique
            base_slug = slugify(product.name) or "produit"
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            product.slug = slug
            product.save()

            messages.success(request, f"Le produit '{product.name}' a été ajouté à votre catalogue !")
            return redirect("merchants:products")
    else:
        form = ProductForm()

    return render(request, "merchant/product_form.html", {"form": form, "merchant": merchant})


@login_required
@merchant_required
def campaigns_list_view(request):
    """Liste de toutes les campagnes lancées par le commerçant."""
    merchant = get_merchant_by_user(request.user)
    campaigns_qs = (
        Campaign.objects.filter(merchant=merchant)
        .select_related("product", "product__store__country__currency")
        .prefetch_related("tiers")
        .order_by("-created_at")
    )
    campaigns_with_summary = []
    for c in campaigns_qs:
        campaigns_with_summary.append({
            "campaign": c,
            "summary": get_campaign_summary(c),
        })

    return render(request, "merchant/campaigns.html", {"campaigns": campaigns_with_summary, "merchant": merchant})


@login_required
@merchant_required
def campaign_create_view(request):
    """Création d'une nouvelle campagne collective avec configuration dynamique des paliers dégressifs."""
    merchant = get_merchant_by_user(request.user)

    if request.method == "POST":
        form = CampaignCreateForm(request.POST, merchant=merchant)
        if form.is_valid():
            product = form.cleaned_data["product"]
            title = form.cleaned_data["title"]
            pricing_policy = form.cleaned_data["pricing_policy"]
            target_participants = form.cleaned_data["target_participants"]
            duration_days = form.cleaned_data["days_duration"]
            terms = form.cleaned_data["terms"]

            # Récupération des paliers depuis le formulaire POST
            tier_mins = request.POST.getlist("tier_min[]")
            tier_maxs = request.POST.getlist("tier_max[]")
            tier_prices = request.POST.getlist("tier_price[]")

            if not tier_prices or len(tier_prices) < 2:
                messages.error(request, "Une campagne collective doit comporter au moins 2 paliers de prix dégressifs.")
            else:
                try:
                    # Validation des paliers
                    parsed_tiers = []
                    last_price = product.original_price
                    for i in range(len(tier_prices)):
                        min_p = int(tier_mins[i])
                        max_p = int(tier_maxs[i]) if tier_maxs[i].strip() else None
                        price = Decimal(tier_prices[i])

                        if price < product.minimum_price:
                            raise ValidationError(f"Le prix du palier ({price}) ne peut pas être inférieur au prix plancher minimum du produit ({product.minimum_price}).")

                        if i == 0 and price > product.original_price:
                            raise ValidationError(f"Le premier palier ({price}) ne peut pas dépasser le prix d'origine du produit ({product.original_price}).")

                        if i > 0 and price >= last_price:
                            raise ValidationError("Chaque palier de volume supérieur doit proposer un prix strictement inférieur au palier précédent.")

                        disc_pct = Decimal("0.00")
                        if product.original_price > 0:
                            disc_pct = (((product.original_price - price) / product.original_price) * 100).quantize(Decimal("0.01"))

                        parsed_tiers.append((min_p, max_p, price, disc_pct))
                        last_price = price


                    # Création de la campagne
                    now = timezone.now()
                    base_slug = slugify(title) or f"campagne-{now.strftime('%Y%m%d%H%M')}"
                    slug = base_slug
                    counter = 1
                    while Campaign.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    campaign = Campaign.objects.create(
                        product=product,
                        merchant=merchant,
                        creator=request.user,
                        title=title,
                        slug=slug,
                        status=CampaignStatus.ACTIVE,
                        pricing_policy=pricing_policy,
                        target_participants=target_participants,
                        min_participants=parsed_tiers[0][0],
                        current_participants_count=0,
                        current_price=product.original_price,
                        start_date=now,
                        end_date=now + timedelta(days=duration_days),
                        terms=terms,
                    )

                    # Enregistrement des PriceTiers
                    for min_p, max_p, price, disc in parsed_tiers:
                        PriceTier.objects.create(
                            campaign=campaign,
                            min_participants=min_p,
                            max_participants=max_p,
                            price=price,
                            discount_percentage=disc,
                        )

                    messages.success(request, f"La campagne collective '{campaign.title}' est désormais active et ouverte aux acheteurs !")
                    return redirect("merchants:campaigns")

                except (ValueError, ValidationError) as e:
                    messages.error(request, str(e))
    else:
        form = CampaignCreateForm(merchant=merchant)

    return render(request, "merchant/campaign_form.html", {"form": form, "merchant": merchant})


@login_required
@merchant_required
def merchant_campaign_detail_view(request, campaign_id):
    """Détail de la campagne pour le commerçant (suivi des participants et du palier en cours)."""
    merchant = get_merchant_by_user(request.user)
    campaign = get_object_or_404(
        Campaign.objects.select_related("product", "product__store__country__currency").prefetch_related("tiers", "participants"),
        pk=campaign_id,
        merchant=merchant,
    )
    summary = get_campaign_summary(campaign)
    participants = campaign.participants.select_related("user").order_by("-joined_at")

    context = {
        "campaign": campaign,
        "summary": summary,
        "participants": participants,
        "merchant": merchant,
    }
    return render(request, "merchant/campaign_detail.html", context)


@login_required
@merchant_required
def merchant_orders_view(request):
    """Gestion des commandes passées sur les campagnes du commerçant."""
    merchant = get_merchant_by_user(request.user)
    status_filter = request.GET.get("status")

    orders_qs = (
        Order.objects.filter(campaign__merchant=merchant)
        .select_related("buyer", "campaign", "currency")
        .order_by("-created_at")
    )
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    return render(
        request,
        "merchant/orders.html",
        {
            "orders": orders_qs,
            "merchant": merchant,
            "current_status": status_filter,
            "order_statuses": OrderStatus.choices,
        },
    )


@login_required
@merchant_required
def merchant_order_detail_view(request, order_number):
    """Détail d'une commande client et mise à jour du statut d'expédition."""
    merchant = get_merchant_by_user(request.user)
    order = get_object_or_404(
        Order.objects.select_related("buyer", "campaign", "currency").prefetch_related("items", "status_history"),
        order_number=order_number,
        campaign__merchant=merchant,
    )

    if request.method == "POST":
        form = OrderStatusUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data["status"]
            notes = form.cleaned_data["notes"]
            try:
                transition_order_status(
                    order=order,
                    new_status=new_status,
                    actor=request.user,
                    notes=notes or f"Mise à jour par le commerçant : {order.get_status_display()}",
                )
                messages.success(request, f"Le statut de la commande #{order.order_number} a été mis à jour vers '{order.get_status_display()}'.")
                return redirect("merchants:order_detail", order_number=order.order_number)
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = OrderStatusUpdateForm(initial={"status": order.status})

    return render(
        request,
        "merchant/order_detail.html",
        {
            "order": order,
            "form": form,
            "merchant": merchant,
            "items": order.items.all(),
            "history": order.status_history.all().order_by("-created_at"),
        },
    )


@login_required
@merchant_required
def revenue_view(request):
    """Suivi financier, volume des ventes et commissions plateforme."""
    merchant = get_merchant_by_user(request.user)
    stats = get_merchant_stats(merchant)

    paid_orders = (
        Order.objects.filter(
            campaign__merchant=merchant,
            status__in=[OrderStatus.PAID, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.DELIVERED],
        )
        .select_related("currency", "campaign")
        .order_by("-created_at")
    )

    return render(
        request,
        "merchant/revenue.html",
        {
            "merchant": merchant,
            "stats": stats,
            "paid_orders": paid_orders,
        },
    )


@login_required
@merchant_required
def statistics_view(request):
    """Statistiques avancées de conversion et performance commerciale."""
    merchant = get_merchant_by_user(request.user)
    stats = get_merchant_stats(merchant)
    return render(request, "merchant/statistics.html", {"merchant": merchant, "stats": stats})


@login_required
@merchant_required
def store_settings_view(request):
    """Paramètres et coordonnées de la boutique."""
    merchant = get_merchant_by_user(request.user)
    store = merchant.stores.first()

    if request.method == "POST" and store:
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, "Les paramètres de votre boutique ont été mis à jour avec succès.")
            return redirect("merchants:store")
    else:
        form = StoreForm(instance=store) if store else None

    return render(request, "merchant/store.html", {"merchant": merchant, "store": store, "form": form})


@login_required
@merchant_required
def verification_view(request):
    """Soumission et consultation des documents d'accréditation commerçant."""
    merchant = get_merchant_by_user(request.user)

    if request.method == "POST":
        doc_type = request.POST.get("document_type", "Registre de Commerce / CNI")
        doc_file = request.FILES.get("document_file")
        if doc_file:
            submit_verification_document(merchant, doc_type, doc_file, user=request.user)
            messages.success(request, "Votre document a été soumis avec succès. Notre équipe va l'examiner sous 24h.")
            return redirect("merchants:verification")
        else:
            messages.error(request, "Veuillez sélectionner un document valide.")

    verifications = merchant.verifications.all().order_by("-submitted_at")
    return render(request, "merchant/settings.html", {"merchant": merchant, "verifications": verifications})
