from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from apps.orders.selectors import get_order_by_number
from .models import Payment, PaymentStatus
from .providers.mock import MockPaymentProvider
from .services import handle_webhook, initiate_payment


@login_required
def payment_selection_view(request):
    order_number = request.GET.get("order") or request.POST.get("order")
    if not order_number:
        messages.error(request, "Numéro de commande manquant.")
        return redirect("orders:buyer_orders")

    order = get_order_by_number(order_number, user=request.user)
    if not order:
        return render(request, "errors/404.html", status=404)

    if order.status != "PENDING":
        messages.info(request, f"Cette commande a déjà été traitée (Statut : {order.get_status_display()}).")
        return redirect("orders:detail", order_number=order.order_number)

    if request.method == "POST":
        method = request.POST.get("payment_method", "mobile_money")
        provider_code = request.POST.get("provider", "mock")
        try:
            payment, redirect_url = initiate_payment(
                order=order,
                provider_code=provider_code,
                payment_method=method,
                user=request.user,
            )
            return redirect(redirect_url)
        except (ValidationError, ValueError) as e:
            messages.error(request, str(e))

    context = {
        "order": order,
        "debug": settings.DEBUG,
    }
    return render(request, "checkout/payment.html", context)


@login_required
def payment_pending_view(request, order_number):
    order = get_order_by_number(order_number, user=request.user)
    if not order:
        return render(request, "errors/404.html", status=404)

    latest_payment = order.payments.order_by("-created_at").first()

    # Si l'utilisateur clique sur 'Simuler la confirmation webhook' en mode DEBUG
    if request.method == "POST" and settings.DEBUG and request.POST.get("simulate_confirm"):
        import json
        import secrets
        mock_prov = MockPaymentProvider()
        event_id = f"EVT-{secrets.token_hex(4).upper()}"
        payload = {
            "event_id": event_id,
            "event_type": "payment.succeeded",
            "data": {
                "reference": latest_payment.reference,
                "status": "SUCCESS",
                "amount": str(latest_payment.amount),
                "currency": latest_payment.currency.code,
            },
        }
        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = mock_prov.generate_test_signature(payload_bytes)

        ok, msg, code = handle_webhook("mock", payload_bytes, signature)
        if ok:
            messages.success(request, "Confirmation webhook simulée avec succès ! Commande validée.")
            return redirect("payments:success", order_number=order.order_number)
        else:
            messages.error(request, f"Erreur de simulation : {msg}")

    context = {
        "order": order,
        "payment": latest_payment,
        "debug": settings.DEBUG,
    }
    return render(request, "checkout/payment_pending.html", context)


@login_required
def payment_success_view(request, order_number):
    order = get_order_by_number(order_number, user=request.user)
    if not order:
        return render(request, "errors/404.html", status=404)

    context = {
        "order": order,
    }
    return render(request, "checkout/payment_success.html", context)


@login_required
def payment_failed_view(request, order_number):
    order = get_order_by_number(order_number, user=request.user)
    if not order:
        return render(request, "errors/404.html", status=404)

    context = {
        "order": order,
    }
    return render(request, "checkout/payment_failed.html", context)


@csrf_exempt
def payment_webhook_view(request, provider_code):
    if request.method != "POST":
        return HttpResponse("Méthode non autorisée", status=405)

    signature = (
        request.headers.get("X-Signature")
        or request.headers.get("X-Webhook-Signature")
        or request.META.get("HTTP_X_SIGNATURE", "")
    )

    payload_bytes = request.body
    success, message, status_code = handle_webhook(
        provider_code=provider_code,
        payload_bytes=payload_bytes,
        signature=signature,
    )

    return JsonResponse({"success": success, "message": message}, status=status_code)
