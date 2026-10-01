from decimal import Decimal
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from apps.campaigns.models import CampaignParticipantStatus
from apps.core.models import AuditLog
from .models import Order, OrderItem, OrderStatus, OrderStatusHistory
from .numbering import generate_order_number
from .state_machine import transition_order_status


@transaction.atomic
def create_order_from_participation(participant, shipping_address, contact_phone, delivery_fee=Decimal("0.00"), user=None):
    if not participant:
        raise ValidationError("Participation invalide.")

    # Vérification d'autorisation
    if user and user != participant.user and not getattr(user, "is_admin", False):
        raise PermissionDenied("Vous n'êtes pas autorisé à créer une commande pour cette participation.")

    # Vérification unicité : une participation ne peut engendrer qu'une seule commande
    if hasattr(participant, "order") and participant.order is not None:
        return participant.order

    campaign = participant.campaign
    product = campaign.product
    currency = product.store.country.currency

    # Le prix unitaire est impérativement certifié côté serveur depuis la campagne/paliers
    unit_price = Decimal(str(campaign.current_price))
    quantity = participant.quantity
    total_amount = unit_price * Decimal(str(quantity))
    delivery_fee = Decimal(str(delivery_fee))
    final_amount = total_amount + delivery_fee

    # Calcul de l'économie réalisée par rapport au prix unitaire d'origine
    original_total = product.original_price * Decimal(str(quantity))
    discount_amount = max(Decimal("0.00"), original_total - total_amount)

    order_number = generate_order_number()

    order = Order.objects.create(
        order_number=order_number,
        buyer=participant.user,
        campaign=campaign,
        campaign_participant=participant,
        currency=currency,
        total_amount=total_amount,
        discount_amount=discount_amount,
        delivery_fee=delivery_fee,
        final_amount=final_amount,
        status=OrderStatus.PENDING,
        shipping_address=shipping_address,
        contact_phone=contact_phone,
    )

    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_amount,
    )

    OrderStatusHistory.objects.create(
        order=order,
        old_status="",
        new_status=OrderStatus.PENDING,
        notes="Commande initiée depuis la participation collective.",
        created_by=participant.user,
    )

    # Confirmer la participation
    participant.status = CampaignParticipantStatus.CONFIRMED
    participant.save(update_fields=["status"])

    AuditLog.objects.create(
        actor=user or participant.user,
        action="ORDER_CREATED_FROM_PARTICIPATION",
        content_object=order,
        changes={
            "order_number": order_number,
            "final_amount": str(final_amount),
            "campaign_id": campaign.id,
        },
    )
    return order


def cancel_order(order, actor, reason=""):
    if order.status != OrderStatus.PENDING and not getattr(actor, "is_admin", False):
        raise ValidationError("Seule une commande en attente peut être annulée directement.")

    return transition_order_status(
        order=order,
        new_status=OrderStatus.CANCELLED,
        actor=actor,
        notes=f"Annulation : {reason}",
    )
