from django.urls import path
from . import views_dashboard

app_name = "dashboard"

urlpatterns = [
    path("", views_dashboard.dashboard_index, name="index"),
    path("campaigns/", views_dashboard.dashboard_campaigns, name="campaigns"),
    path("orders/", views_dashboard.dashboard_orders, name="orders"),
    path("profile/", views_dashboard.dashboard_profile, name="profile"),
    path("notifications/", views_dashboard.dashboard_notifications, name="notifications"),
]
