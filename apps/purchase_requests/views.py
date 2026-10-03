from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from apps.countries.models import Country
from apps.catalog.models import Category
from .forms import JoinPurchaseRequestForm, PurchaseRequestCreateForm, SellerProposalForm
from .models import PurchaseRequest, PurchaseRequestParticipant, RequestStatus, SellerProposal
from .selectors import get_active_purchase_requests, get_purchase_request_detail
from .services import (
    accept_seller_proposal,
    create_purchase_request,
    create_seller_proposal,
    join_purchase_request,
)


def purchase_request_list(request):
    country_code = request.GET.get("country", "")
    category_id = request.GET.get("category", "")

    requests_qs = get_active_purchase_requests(
        country_code=country_code if country_code else None,
        category_id=category_id if category_id else None,
    )

    countries = Country.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)

    return render(
        request,
        "purchase_requests/request_list.html",
        {
            "requests": requests_qs,
            "countries": countries,
            "categories": categories,
            "selected_country": country_code,
            "selected_category": int(category_id) if category_id.isdigit() else None,
        },
    )


def purchase_request_detail(request, pk):
    pr = get_purchase_request_detail(pk)
    if not pr:
        messages.error(request, "Demande groupée introuvable.")
        return redirect("purchase_requests:list")

    user_has_joined = False
    user_pledged_qty = 0
    if request.user.is_authenticated:
        pledge = pr.participants.filter(user=request.user).first()
        if pledge:
            user_has_joined = True
            user_pledged_qty = pledge.quantity_pledged

    is_creator = request.user.is_authenticated and (request.user == pr.creator or getattr(request.user, "is_admin", False))
    merchant = getattr(request.user, "merchant_profile", None) if request.user.is_authenticated else None
    can_submit_proposal = bool(merchant and merchant.is_verified and pr.status in [RequestStatus.OPEN, RequestStatus.PROPOSALS_RECEIVED])

    join_form = JoinPurchaseRequestForm()

    return render(
        request,
        "purchase_requests/request_detail.html",
        {
            "request_obj": pr,
            "user_has_joined": user_has_joined,
            "user_pledged_qty": user_pledged_qty,
            "is_creator": is_creator,
            "can_submit_proposal": can_submit_proposal,
            "merchant": merchant,
            "join_form": join_form,
        },
    )


@login_required
def purchase_request_create(request):
    if request.method == "POST":
        form = PurchaseRequestCreateForm(request.POST)
        if form.is_valid():
            try:
                days = int(form.cleaned_data["duration_days"])
                expires_at = timezone.now() + timedelta(days=days)
                pr = create_purchase_request(
                    creator=request.user,
                    country=form.cleaned_data["country"],
                    category=form.cleaned_data.get("category"),
                    title=form.cleaned_data["title"],
                    description=form.cleaned_data["description"],
                    target_quantity=form.cleaned_data["target_quantity"],
                    target_price=form.cleaned_data["target_price"],
                    expires_at=expires_at,
                )
                messages.success(request, f"Votre demande groupée « {pr.title} » a été publiée avec succès !")
                return redirect("purchase_requests:detail", pk=pr.pk)
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, str(exc))
    else:
        form = PurchaseRequestCreateForm()

    return render(request, "purchase_requests/request_create.html", {"form": form})


@login_required
def purchase_request_join(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == "POST":
        form = JoinPurchaseRequestForm(request.POST)
        if form.is_valid():
            try:
                qty = form.cleaned_data["quantity_pledged"]
                join_purchase_request(purchase_request=pr, user=request.user, quantity_pledged=qty)
                messages.success(request, f"Félicitations ! Vous avez rejoint cette demande pour {qty} unité(s).")
                return redirect("purchase_requests:detail", pk=pr.pk)
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, str(exc))
                return redirect("purchase_requests:detail", pk=pr.pk)
    return render(request, "purchase_requests/request_join.html", {"pr": pr})



@login_required
def seller_proposal_create(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    merchant = getattr(request.user, "merchant_profile", None)

    if not merchant or not merchant.is_verified:
        messages.error(request, "Seuls les commerçants vérifiés peuvent déposer des propositions formelles.")
        return redirect("purchase_requests:detail", pk=pr.pk)

    if request.method == "POST":
        form = SellerProposalForm(request.POST, merchant=merchant)
        if form.is_valid():
            try:
                days = int(form.cleaned_data["validity_days"])
                valid_until = timezone.now() + timedelta(days=days)
                proposal = create_seller_proposal(
                    purchase_request=pr,
                    merchant=merchant,
                    store=form.cleaned_data["store"],
                    proposed_price=form.cleaned_data["proposed_price"],
                    min_quantity=form.cleaned_data["min_quantity"],
                    description=form.cleaned_data.get("description", ""),
                    valid_until=valid_until,
                )
                messages.success(request, f"Votre offre commerciale de {proposal.proposed_price} FCFA a été transmise aux acheteurs !")
                return redirect("purchase_requests:detail", pk=pr.pk)
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, str(exc))
    else:
        form = SellerProposalForm(merchant=merchant)

    return render(
        request,
        "purchase_requests/proposal_create.html",
        {"form": form, "request_obj": pr, "merchant": merchant},
    )


@login_required
def seller_proposal_accept(request, pk, proposal_id):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    proposal = get_object_or_404(SellerProposal, pk=proposal_id, purchase_request=pr)

    if request.method == "POST":
        try:
            accept_seller_proposal(purchase_request=pr, proposal=proposal, user=request.user)
            messages.success(
                request,
                f"L'offre de {proposal.merchant.business_name} au prix de {proposal.proposed_price} FCFA a été validée !",
            )
        except (ValidationError, PermissionDenied) as exc:
            messages.error(request, str(exc))

    return redirect("purchase_requests:detail", pk=pr.pk)
