from decimal import Decimal
import json
import secrets
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from apps.core.models import AuditLog
from apps.orders.models import OrderStatus
from apps.orders.state_machine import transition_order_status
from .models import Payment, PaymentProvider, PaymentStatus, PaymentTransaction, WebhookEvent
from .providers.registry import registry


def initiate_payment(order, provider_code="mock", payment_method="mobile_money", user=None):
    if order.status != OrderStatus.PENDING:
        raise ValidationError(f"Cette commande n'est pas en attente de paiement (Statut : {order.get_status_display()}).")

    provider_instance = registry.get_provider(provider_code)

    # Récupérer ou créer l'entrée en base pour le provider
    db_provider, _ = PaymentProvider.objects.get_or_create(
        code=provider_code,
        defaults={"name": provider_instance.name, "is_active": True},
    )

    # Clé d'idempotence unique
    idempotency_key = f"PAY-{order.order_number}-{secrets.token_hex(4).upper()}"

    payment = Payment.objects.create(
        order=order,
        provider=db_provider,
        payment_method=payment_method,
        amount=order.final_amount,
        currency=order.currency,
        status=PaymentStatus.PENDING,
        idempotency_key=idempotency_key,
        reference=idempotency_key,
    )

    # Appel au provider
    return_url = f"/payment/success/{order.order_number}/"
    cancel_url = f"/payment/failed/{order.order_number}/"
    result = provider_instance.initialize_payment(payment, return_url, cancel_url)

    # Mettre à jour la référence retournée par le prestataire si applicable
    if result.provider_reference:
        payment.reference = result.provider_reference
        payment.save(update_fields=["reference"])

    PaymentTransaction.objects.create(
        payment=payment,
        transaction_type="PAYMENT",
        amount=payment.amount,
        provider_reference=result.provider_reference,
        raw_response=result.raw_data,
        status=PaymentStatus.PENDING,
    )

    AuditLog.objects.create(
        actor=user or order.buyer,
        action="PAYMENT_INITIATED",
        content_object=payment,
        changes={"amount": str(payment.amount), "provider": provider_code},
    )
    return payment, result.payment_url


@transaction.atomic
def handle_webhook(provider_code: str, payload_bytes: bytes, signature: str):
    """
    Gestionnaire unifié et sécurisé des webhooks de paiement.
    Vérifie la signature, l'idempotence, compare montants et devises et valide la commande côté serveur.
    """
    provider_instance = registry.get_provider(provider_code)

    # 1. Vérification cryptographique de la signature
    if not provider_instance.verify_webhook_signature(payload_bytes, signature):
        AuditLog.objects.create(
            actor=None,
            action="WEBHOOK_INVALID_SIGNATURE",
            changes={"provider": provider_code, "signature": signature},
        )
        return False, "Signature cryptographique invalide.", 401

    try:
        payload_dict = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        return False, f"Payload JSON malformé : {e}", 400

    parsed = provider_instance.parse_webhook_event(payload_dict)

    db_provider, _ = PaymentProvider.objects.get_or_create(
        code=provider_code,
        defaults={"name": provider_instance.name, "is_active": True},
    )

    # 2. Vérification d'Idempotence stricte (Protection contre les doubles écritures / rejeu)
    webhook_event, created = WebhookEvent.objects.get_or_create(
        provider=db_provider,
        event_id=parsed.event_id,
        defaults={
            "event_type": parsed.event_type,
            "payload": payload_dict,
            "processed": False,
        },
    )

    if not created and webhook_event.processed:
        return True, "Événement déjà traité précédemment (Idempotence respectée).", 200

    # 3. Retrouver le paiement associé
    payment = (
        Payment.objects.filter(reference=parsed.reference)
        .select_for_update()
        .first()
    )
    if not payment:
        payment = Payment.objects.filter(idempotency_key=parsed.reference).select_for_update().first()

    if not payment:
        webhook_event.error = f"Paiement introuvable pour la référence '{parsed.reference}'."
        webhook_event.save(update_fields=["error"])
        return False, "Paiement introuvable.", 404

    # 4. Vérification d'intégrité : montant et devise confirmés par le webhook vs attendus
    if payment.amount != parsed.amount or payment.currency.code != parsed.currency:
        error_msg = (
            f"Écart détecté ! Attendu : {payment.amount} {payment.currency.code} | "
            f"Reçu : {parsed.amount} {parsed.currency}"
        )
        webhook_event.error = error_msg
        webhook_event.save(update_fields=["error"])

        AuditLog.objects.create(
            actor=None,
            action="PAYMENT_AMOUNT_MISMATCH_ALERT",
            content_object=payment,
            changes={"expected": f"{payment.amount} {payment.currency.code}", "received": f"{parsed.amount} {parsed.currency}"},
        )
        return False, "Incohérence du montant ou de la devise.", 400

    # 5. Traitement du statut
    if parsed.status == "SUCCESS":
        payment.status = PaymentStatus.SUCCESS
        payment.save(update_fields=["status"])

        # Mettre à jour la transaction
        tx = payment.transactions.first()
        if tx:
            tx.status = PaymentStatus.SUCCESS
            tx.save(update_fields=["status"])

        # Validation de la commande côté serveur
        transition_order_status(
            order=payment.order,
            new_status=OrderStatus.PAID,
            notes=f"Payé via webhook {provider_code} (Événement #{parsed.event_id})",
        )

        # Calcul et enregistrement de la commission plateforme
        try:
            from apps.commissions.services import record_commission
            record_commission(order=payment.order, actor=None)
        except Exception:
            pass  # La commission ne bloque jamais la confirmation du paiement

        AuditLog.objects.create(
            actor=None,
            action="PAYMENT_SUCCESS_CONFIRMED",
            content_object=payment,
            changes={"order_number": payment.order.order_number, "event_id": parsed.event_id},
        )

    elif parsed.status in ["FAILED", "CANCELLED"]:
        payment.status = PaymentStatus.FAILED
        payment.save(update_fields=["status"])

    webhook_event.processed = True
    webhook_event.save(update_fields=["processed"])

    return True, "Webhook traité avec succès.", 200
