from django.conf import settings


def platform(request):
    ctx = {
        "PLATFORM_NAME": getattr(settings, "PLATFORM_NAME", "REDUX"),
        "DEFAULT_COUNTRY_CODE": getattr(settings, "DEFAULT_COUNTRY_CODE", "BJ"),
        "unread_notifications_count": 0,
    }
    if request.user.is_authenticated:
        try:
            ctx["unread_notifications_count"] = request.user.notifications.filter(is_read=False).count()
        except Exception:
            pass
    return ctx
