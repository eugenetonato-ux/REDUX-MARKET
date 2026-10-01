from django.core.exceptions import ValidationError
from apps.core.models import AuditLog
from .models import OrderStatus, OrderStatusHistory


VALID_ORDER_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID: [OrderStatus.PROCESSING, OrderStatus.REFUNDED, OrderStatus.CANCELLED],
    OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED, OrderStatus.REFUNDED],
    OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.REFUNDED],
    OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
    OrderStatus.CANCELLED: [],
    OrderStatus.REFUNDED: [],
}


def transition_order_status(order, new_status, actor=None, notes=""):
    current = order.status
    if current == new_status:
        return order

    allowed = VALID_ORDER_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Transition de commande invalide : impossible de passer de '{current}' à '{new_status}'."
        )

    order.status = new_status
    order.save(update_fields=["status"])

    OrderStatusHistory.objects.create(
        order=order,
        old_status=current,
        new_status=new_status,
        notes=notes,
        created_by=actor,
    )

    AuditLog.objects.create(
        actor=actor,
        action="ORDER_STATUS_TRANSITION",
        content_object=order,
        changes={"old_status": current, "new_status": new_status, "notes": notes},
    )
    return order
