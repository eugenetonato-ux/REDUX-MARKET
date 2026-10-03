"""
Notifications KYC/Vérification commerçant REDUX.

Fonctions déclenchées quand un admin valide ou rejette un dossier KYC.
Envoie une notification in-app + email au commerçant concerné.
"""
from apps.notifications.dispatcher import send_notification


def notify_merchant_kyc_approved(merchant):
    """
    Notifie le commerçant que son dossier KYC a été approuvé.
    Son badge « Commerçant Vérifié » est maintenant actif.

    Args:
        merchant : instance MerchantProfile
    """
    user = merchant.user
    send_notification(
        recipient=user,
        title="Félicitations ! Votre boutique est vérifiée",
        message=(
            f"Votre dossier de vérification pour « {merchant.business_name} » a été approuvé. "
            f"Votre badge Commerçant Vérifié est désormais actif. "
            f"Vous pouvez maintenant créer des campagnes collectives qui seront activées immédiatement."
        ),
        notification_type="kyc_approved",
        link="/merchant/dashboard/",
    )


def notify_merchant_kyc_rejected(merchant, reason=""):
    """
    Notifie le commerçant que son dossier KYC a été rejeté.
    Inclut le motif de rejet si disponible.

    Args:
        merchant : instance MerchantProfile
        reason   : texte explicatif du rejet (optionnel)
    """
    user = merchant.user
    reason_text = f"\n\nMotif : {reason}" if reason else ""
    send_notification(
        recipient=user,
        title="Dossier de vérification refusé",
        message=(
            f"Votre dossier de vérification pour « {merchant.business_name} » n'a pas pu être validé. "
            f"Veuillez vérifier vos documents et soumettre à nouveau votre dossier depuis votre espace commerçant."
            f"{reason_text}"
        ),
        notification_type="kyc_rejected",
        link="/merchant/verification/",
    )


def notify_merchant_kyc_document_received(merchant, document_type):
    """
    Accusé de réception envoyé au commerçant dès qu'il soumet un document.
    Lui confirme que son dossier est bien en cours d'examen.

    Args:
        merchant      : instance MerchantProfile
        document_type : type de document soumis (ex: "Carte d'identité", "RCCM")
    """
    user = merchant.user
    send_notification(
        recipient=user,
        title="Document KYC reçu — en cours d'examen",
        message=(
            f"Nous avons bien reçu votre document « {document_type} » pour "
            f"« {merchant.business_name} ». "
            f"Notre équipe examine votre dossier sous 24-48h ouvrées. "
            f"Vous serez notifié dès que la vérification sera effectuée."
        ),
        notification_type="kyc_document_received",
        link="/merchant/verification/",
    )


def notify_admin_kyc_pending(merchant, document_type, admin_users=None):
    """
    Notifie les admins qu'un nouveau document KYC vient d'être soumis.
    Permet une réaction rapide sans avoir à surveiller l'admin en permanence.

    Args:
        merchant      : instance MerchantProfile
        document_type : type de document soumis
        admin_users   : queryset ou liste d'admins à notifier
    """
    if not admin_users:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_users = User.objects.filter(is_staff=True, is_active=True)

    for admin in admin_users:
        send_notification(
            recipient=admin,
            title=f"Nouveau dossier KYC en attente — {merchant.business_name}",
            message=(
                f"Le commerçant « {merchant.business_name} » (email: {merchant.user.email}) "
                f"a soumis un document « {document_type} » pour vérification. "
                f"Veuillez examiner le dossier depuis le panneau d'administration."
            ),
            notification_type="admin_kyc_pending",
            link="/cpanel-redux/merchants/merchantverification/?status__exact=PENDING",
        )
