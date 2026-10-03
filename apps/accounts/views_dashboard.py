from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from apps.accounts.decorators import buyer_required
from apps.accounts.forms import ProfileForm
from apps.campaigns.models import CampaignParticipant
from apps.orders.models import Order


@login_required
@buyer_required
def dashboard_index(request):
    """Tableau de bord principal de l'acheteur."""
    user = request.user
    profile = getattr(user, "buyer_profile", None)

    participations = (
        CampaignParticipant.objects.filter(user=user)
        .select_related("campaign", "campaign__product", "campaign__product__store", "campaign__product__store__country__currency")
        .order_by("-joined_at")[:5]
    )

    orders = (
        Order.objects.filter(buyer=user)
        .select_related("campaign", "currency")
        .order_by("-created_at")[:5]
    )

    total_participations = CampaignParticipant.objects.filter(user=user).count()
    total_orders = Order.objects.filter(buyer=user).count()

    context = {
        "user": user,
        "profile": profile,
        "participations": participations,
        "orders": orders,
        "total_participations": total_participations,
        "total_orders": total_orders,
    }
    return render(request, "dashboard/index.html", context)


@login_required
@buyer_required
def dashboard_campaigns(request):
    """Historique complet des participations aux campagnes de groupe."""
    user = request.user
    participations = (
        CampaignParticipant.objects.filter(user=user)
        .select_related("campaign", "campaign__product", "campaign__product__store", "campaign__product__store__country__currency")
        .order_by("-joined_at")
    )
    return render(request, "dashboard/campaigns.html", {"participations": participations})


@login_required
@buyer_required
def dashboard_orders(request):
    """Historique des commandes de l'acheteur."""
    user = request.user
    orders = (
        Order.objects.filter(buyer=user)
        .select_related("campaign", "currency")
        .order_by("-created_at")
    )
    return render(request, "dashboard/orders.html", {"orders": orders})


@login_required
@buyer_required
def dashboard_profile(request):
    """Modification du profil et de l'adresse de livraison de l'acheteur."""
    user = request.user
    profile = getattr(user, "buyer_profile", None)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        shipping_address = request.POST.get("shipping_address", "").strip()
        city = request.POST.get("city", "").strip()

        if form.is_valid():
            form.save()
            if profile:
                profile.default_shipping_address = shipping_address
                profile.city = city
                profile.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect("dashboard:profile")
    else:
        form = ProfileForm(instance=user)

    return render(
        request,
        "dashboard/profile.html",
        {
            "form": form,
            "profile": profile,
        },
    )


@login_required
@buyer_required
def dashboard_notifications(request):
    """Notifications de l'acheteur."""
    notifications = []
    return render(request, "dashboard/notifications.html", {"notifications": notifications})
