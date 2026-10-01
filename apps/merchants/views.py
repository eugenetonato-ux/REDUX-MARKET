from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import VerificationStatus
from .selectors import get_merchant_by_user, get_merchant_stats
from .services import create_merchant_profile, submit_verification_document


@login_required
def dashboard_view(request):
    merchant = get_merchant_by_user(request.user)
    if not merchant:
        # Si l'utilisateur n'a pas encore de profil commerçant, on l'initialise
        merchant = create_merchant_profile(
            user=request.user,
            business_name=f"Boutique de {request.user.full_name or request.user.email}",
        )

    stats = get_merchant_stats(merchant)
    stores = merchant.stores.all()

    context = {
        "merchant": merchant,
        "stats": stats,
        "stores": stores,
    }
    return render(request, "merchant/dashboard.html", context)


@login_required
def verification_view(request):
    merchant = get_merchant_by_user(request.user)
    if not merchant:
        return redirect("merchants:dashboard")

    if request.method == "POST":
        doc_type = request.POST.get("document_type", "Registre de Commerce / CNI")
        doc_file = request.FILES.get("document_file")
        if doc_file:
            submit_verification_document(merchant, doc_type, doc_file, user=request.user)
            messages.success(request, "Votre document a été soumis avec succès. Notre équipe va l'examiner sous 24h.")
            return redirect("merchants:verification")
        else:
            messages.error(request, "Veuillez sélectionner un fichier valide.")

    verifications = merchant.verifications.all().order_by("-submitted_at")
    context = {
        "merchant": merchant,
        "verifications": verifications,
    }
    return render(request, "merchant/settings.html", context)


@login_required
def store_settings_view(request):
    merchant = get_merchant_by_user(request.user)
    if not merchant:
        return redirect("merchants:dashboard")

    stores = merchant.stores.all()
    context = {
        "merchant": merchant,
        "stores": stores,
    }
    return render(request, "merchant/store.html", context)
