from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list_view, name="list"),
    path("<int:notification_id>/read/", views.mark_read_view, name="mark_read"),
]
