from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from apps.orders.models import Order
from .forms import DisputeCreateForm, DisputeMessageForm
from .models import Dispute, DisputeMessage, DisputeStatus


@login_required
def dispute_list_view(request):
    """Liste des litiges ouverts par l'acheteur ou concernant le commerçant."""
    user = request.user
    if user.is_admin:
        disputes = Dispute.objects.all().select_related("order", "opened_by").order_by("-created_at")
    elif user.is_merchant:
        disputes = Dispute.objects.filter(
            Q(opened_by=user) | Q(order__campaign__merchant__user=user)
        ).select_related("order", "opened_by").order_by("-created_at")
    else:
        disputes = Dispute.objects.filter(opened_by=user).select_related("order").order_by("-created_at")

    return render(request, "disputes/dispute_list.html", {"disputes": disputes})


@login_required
def dispute_create_view(request, order_number):
    """Ouverture d'un litige / réclamation sur une commande."""
    order = get_object_or_404(
        Order.objects.select_related("campaign", "campaign__product", "campaign__product__store"),
        order_number=order_number,
    )

    if order.buyer != request.user and not getattr(request.user, "is_admin", False):
        raise PermissionDenied("Vous ne pouvez ouvrir un litige que sur vos propres commandes.")

    # Vérifier si un litige est déjà ouvert
    existing_open = order.disputes.filter(status__in=[DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW]).first()
    if existing_open:
        messages.info(request, "Un litige est déjà en cours d'examen pour cette commande.")
        return redirect("disputes:detail", pk=existing_open.pk)

    if request.method == "POST":
        form = DisputeCreateForm(request.POST)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.order = order
            dispute.opened_by = request.user
            dispute.status = DisputeStatus.OPEN
            dispute.save()

            messages.success(
                request,
                f"Votre réclamation a été transmise. Les fonds sous séquestre pour la commande #{order.order_number} restent bloqués jusqu'à arbitrage."
            )
            return redirect("disputes:detail", pk=dispute.pk)
    else:
        form = DisputeCreateForm()

    return render(
        request,
        "disputes/dispute_form.html",
        {
            "order": order,
            "form": form,
        },
    )


@login_required
def dispute_detail_view(request, pk):
    """Fil de discussion et suivi de résolution du litige."""
    dispute = get_object_or_404(
        Dispute.objects.select_related("order", "opened_by", "order__campaign__product__store"),
        pk=pk,
    )

    # Sécurité d'accès : Acheteur propriétaire, Commerçant concerné ou Admin
    is_buyer = dispute.opened_by == request.user
    is_merchant = getattr(dispute.order.campaign, "merchant", None) and dispute.order.campaign.merchant.user == request.user
    is_admin = getattr(request.user, "is_admin", False)

    if not (is_buyer or is_merchant or is_admin):
        raise PermissionDenied("Vous n'êtes pas autorisé à consulter ce litige.")

    if request.method == "POST":
        msg_form = DisputeMessageForm(request.POST, request.FILES)
        if msg_form.is_valid():
            msg = msg_form.save(commit=False)
            msg.dispute = dispute
            msg.sender = request.user
            msg.save()
            messages.success(request, "Votre message a été ajouté au dossier de réclamation.")
            return redirect("disputes:detail", pk=dispute.pk)
    else:
        msg_form = DisputeMessageForm()

    thread_messages = dispute.messages.select_related("sender").order_by("created_at")

    return render(
        request,
        "disputes/dispute_detail.html",
        {
            "dispute": dispute,
            "order": dispute.order,
            "thread_messages": thread_messages,
            "msg_form": msg_form,
            "is_buyer": is_buyer,
            "is_merchant": is_merchant,
            "is_admin": is_admin,
        },
    )
