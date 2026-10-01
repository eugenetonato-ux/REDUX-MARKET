from .dispatcher import send_notification


def notify_campaign_joined(participant):
    user = participant.user
    camp = participant.campaign
    send_notification(
        recipient=user,
        title="Participation enregistrée !",
        message=f"Vous avez rejoint la campagne collective '{camp.title}' pour {participant.quantity} unité(s). Le prix actuel est de {camp.current_price} {camp.product.store.country.currency.symbol}.",
        notification_type="campaign_joined",
        link=f"/campaigns/{camp.slug}/",
    )


def notify_tier_reached(campaign, new_tier):
    # Notifie tous les participants actifs
    participants = campaign.participants.filter(status="JOINED").select_related("user")
    currency_symbol = campaign.product.store.country.currency.symbol

    for part in participants:
        send_notification(
            recipient=part.user,
            title="🎉 Nouveau palier de réduction débloqué !",
            message=f"Grâce aux nouvelles arrivées dans le groupe, le prix de '{campaign.title}' est tombé à {new_tier.price} {currency_symbol} (-{new_tier.discount_percentage}%).",
            notification_type="tier_reached",
            link=f"/campaigns/{campaign.slug}/",
        )


def notify_order_confirmed(order):
    send_notification(
        recipient=order.buyer,
        title=f"Commande confirmée #{order.order_number}",
        message=f"Votre paiement a été validé ! Votre commande de {order.final_amount} {order.currency.symbol} est en cours de préparation.",
        notification_type="order_confirmed",
        link=f"/order/{order.order_number}/",
    )

    # Notifier le commerçant
    merchant_user = order.campaign.merchant.user if order.campaign else None
    if merchant_user:
        send_notification(
            recipient=merchant_user,
            title=f"Nouvelle commande payée #{order.order_number}",
            message=f"L'acheteur a réglé sa commande ({order.final_amount} {order.currency.symbol}). Veuillez préparer l'expédition.",
            notification_type="merchant_new_order",
            link=f"/merchant/orders/",
        )
