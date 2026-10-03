from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.utils.html import escape
from .models import Notification, NotificationPreference


def get_or_create_preferences(user):
    pref, _ = NotificationPreference.objects.get_or_create(
        user=user,
        defaults={
            "email_notifications": True,
            "in_app_notifications": True,
            "sms_notifications": False,
            "whatsapp_notifications": False,
        },
    )
    return pref


def _send_email(subject: str, body: str, recipient_email: str) -> bool:
    """
    Envoie un email via le mailer Django 6.1+ (MAILERS["default"]).
    Retourne True si l'envoi a réussi, False sinon.
    Remplace send_mail(..., fail_silently=True) — deprecated en Django 6.
    """
    try:
        connection = get_connection(using="default")
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@redux.app"),
            to=[recipient_email],
            connection=connection,
        )
        email.send()
        return True
    except Exception:
        return False


def send_notification(recipient, title, message, notification_type="system", link="", channels=None):
    """
    Distributeur centralisé de notifications avec respect des préférences de l'utilisateur
    et échappement anti-injection.
    """
    if not recipient or not recipient.is_active:
        return None

    pref = get_or_create_preferences(recipient)
    clean_title = escape(title.strip())
    clean_message = escape(message.strip())

    notification_obj = None

    # 1. Canal In-App
    if pref.in_app_notifications:
        notification_obj = Notification.objects.create(
            recipient=recipient,
            title=clean_title,
            message=clean_message,
            notification_type=notification_type,
            link=link,
            is_read=False,
        )

    # 2. Canal Email — via MAILERS Django 6.1+
    if pref.email_notifications and recipient.email:
        platform = getattr(settings, "PLATFORM_NAME", "REDUX")
        _send_email(
            subject=f"[{platform}] {title}",
            body=message,
            recipient_email=recipient.email,
        )

    return notification_obj
