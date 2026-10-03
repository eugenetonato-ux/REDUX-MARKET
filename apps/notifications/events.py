from .dispatcher import send_notification


def notify_campaign_joined(participant):
    user = participant.user
    camp = participant.campaign
    currency_symbol = ""
    try:
        currency_symbol = camp.product.store.country.currency.symbol
    except Exception:
        pass
    send_notification(
        recipient=user,
        title="Participation enregistrée !",
        message=(
            f"Vous avez rejoint la campagne collective « {camp.title} » "
            f"pour {participant.quantity} unité(s). "
            f"Le prix actuel est de {camp.current_price} {currency_symbol}."
        ),
        notification_type="campaign_joined",
        link=f"/campaigns/{camp.slug}/",
    )


def notify_tier_reached(campaign, new_tier):
    """Notifie tous les participants actifs qu'un palier inférieur vient d'être débloqué."""
    participants = campaign.participants.filter(status="JOINED").select_related("user")
    currency_symbol = ""
    try:
        currency_symbol = campaign.product.store.country.currency.symbol
    except Exception:
        pass
    disc_text = f" (-{new_tier.discount_percentage}%)" if getattr(new_tier, "discount_percentage", None) else ""
    for part in participants:
        send_notification(
            recipient=part.user,
            title="🎉 Nouveau palier de réduction débloqué !",
            message=(
                f"Grâce aux nouvelles arrivées dans le groupe, le prix de "
                f"« {campaign.title} » est tombé à {new_tier.price} {currency_symbol}{disc_text}. "
                f"Partagez le lien pour débloquer le palier suivant !"
            ),
            notification_type="tier_reached",
            link=f"/campaigns/{campaign.slug}/",
        )


def notify_order_status_changed(order, old_status):
    """
    Notifie l'acheteur dès qu'une commande change de statut.
    Notifie aussi le commerçant en cas de nouvelle commande payée.
    """
    status = order.status
    currency_symbol = getattr(order.currency, "symbol", order.currency.code)

    status_messages = {
        "PAID": {
            "title": f"✅ Commande confirmée #{order.order_number}",
            "message": (
                f"Votre paiement de {order.final_amount} {currency_symbol} a été validé. "
                f"Votre commande est en cours de préparation par la boutique."
            ),
        },
        "PROCESSING": {
            "title": f"⚙️ Commande en préparation #{order.order_number}",
            "message": (
                f"La boutique prépare votre commande #{order.order_number}. "
                f"Vous serez notifié dès l'expédition."
            ),
        },
        "SHIPPED": {
            "title": f"🚚 Commande expédiée #{order.order_number}",
            "message": (
                f"Votre commande #{order.order_number} a été remise au transporteur. "
                f"Elle est en route vers vous !"
            ),
        },
        "DELIVERED": {
            "title": f"📦 Commande livrée #{order.order_number}",
            "message": (
                f"Votre commande #{order.order_number} a été marquée comme livrée. "
                f"N'hésitez pas à laisser un avis sur la boutique !"
            ),
        },
        "CANCELLED": {
            "title": f"❌ Commande annulée #{order.order_number}",
            "message": (
                f"Votre commande #{order.order_number} a été annulée. "
                f"Contactez-nous si vous avez des questions."
            ),
        },
    }

    if status in status_messages:
        info = status_messages[status]
        send_notification(
            recipient=order.buyer,
            title=info["title"],
            message=info["message"],
            notification_type=f"order_{status.lower()}",
            link=f"/order/{order.order_number}/",
        )

    # Notifier le commerçant uniquement pour les nouvelles commandes payées
    if status == "PAID" and old_status == "PENDING":
        merchant_user = None
        if order.campaign and hasattr(order.campaign, "merchant"):
            merchant_user = order.campaign.merchant.user
        if merchant_user:
            send_notification(
                recipient=merchant_user,
                title=f"💰 Nouvelle commande payée #{order.order_number}",
                message=(
                    f"L'acheteur {order.buyer.full_name or order.buyer.email} a réglé "
                    f"{order.final_amount} {currency_symbol}. "
                    f"Veuillez préparer l'expédition rapidement."
                ),
                notification_type="merchant_new_order",
                link="/merchant/orders/",
            )


def notify_order_confirmed(order):
    """Alias de compatibilité — appel direct depuis payments/services.py."""
    notify_order_status_changed(order, old_status="PENDING")
