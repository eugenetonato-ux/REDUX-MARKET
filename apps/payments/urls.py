from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("payment/", views.payment_selection_view, name="select"),
    path("payment/pending/<str:order_number>/", views.payment_pending_view, name="pending"),
    path("payment/success/<str:order_number>/", views.payment_success_view, name="success"),
    path("payment/failed/<str:order_number>/", views.payment_failed_view, name="failed"),
    path("payments/webhook/<str:provider_code>/", views.payment_webhook_view, name="webhook"),
]
