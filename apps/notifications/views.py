from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Notification


@login_required
def notification_list_view(request):
    notifications = request.user.notifications.all().order_by("-created_at")

    if request.method == "POST" and request.POST.get("mark_all_read"):
        notifications.filter(is_read=False).update(is_read=True)
        return redirect("notifications:list")

    context = {
        "notifications": notifications,
        "unread_count": notifications.filter(is_read=False).count(),
    }
    return render(request, "dashboard/notifications.html", context)


@login_required
def mark_read_view(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=["is_read"])

    if notif.link:
        return redirect(notif.link)
    return redirect("notifications:list")
