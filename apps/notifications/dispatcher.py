from django.conf import settings
from django.core.mail import send_mail
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

    # 2. Canal Email
    if pref.email_notifications and recipient.email:
        try:
            subject = f"[{getattr(settings, 'PLATFORM_NAME', 'REDUX')}] {title}"
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@redux.app"),
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        except Exception:
            pass

    return notification_obj
