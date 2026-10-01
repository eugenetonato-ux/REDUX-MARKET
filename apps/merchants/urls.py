from django.urls import path
from . import views

app_name = "merchants"

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("verification/", views.verification_view, name="verification"),
    path("store/", views.store_settings_view, name="store"),
]
