from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from apps.campaigns.models import CampaignParticipant
from .models import Order
from .selectors import get_order_by_number, list_user_orders
from .services import create_order_from_participation


@login_required
def checkout_view(request, participant_id):
    participant = get_object_or_404(
        CampaignParticipant.objects.select_related(
            "campaign",
            "campaign__product",
            "campaign__product__store",
            "campaign__product__store__country",
            "campaign__product__store__country__currency",
        ),
        pk=participant_id,
    )

    if participant.user != request.user and not request.user.is_admin:
        raise PermissionDenied("Cette participation ne vous appartient pas.")

    # Si la commande existe déjà pour cette participation, rediriger vers sa page
    if hasattr(participant, "order") and participant.order is not None:
        return redirect("orders:detail", order_number=participant.order.order_number)

    if request.method == "POST":
        address = request.POST.get("shipping_address", "").strip()
        phone = request.POST.get("contact_phone", "").strip()

        if not address or not phone:
            messages.error(request, "Veuillez renseigner votre adresse de livraison et numéro de contact.")
        else:
            try:
                order = create_order_from_participation(
                    participant=participant,
                    shipping_address=address,
                    contact_phone=phone,
                    user=request.user,
                )
                messages.success(request, f"Votre commande #{order.order_number} a été initiée avec succès !")
                return redirect("orders:detail", order_number=order.order_number)
            except ValidationError as e:
                messages.error(request, str(e))

    context = {
        "participant": participant,
        "campaign": participant.campaign,
        "product": participant.campaign.product,
        "currency": participant.campaign.product.store.country.currency,
        "total_estimated": participant.quantity * participant.campaign.current_price,
    }
    return render(request, "checkout/checkout.html", context)


@login_required
def order_detail_view(request, order_number):
    order = get_order_by_number(order_number, user=request.user)
    if not order:
        return render(request, "errors/404.html", status=404)

    context = {
        "order": order,
        "items": order.items.all(),
        "history": order.status_history.all(),
    }
    return render(request, "checkout/order_detail.html", context)


@login_required
def buyer_orders_list_view(request):
    orders = list_user_orders(request.user)
    context = {
        "orders": orders,
    }
    return render(request, "dashboard/orders.html", context)
