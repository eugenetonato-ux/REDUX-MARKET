from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/<int:participant_id>/", views.checkout_view, name="checkout"),
    path("order/<str:order_number>/", views.order_detail_view, name="detail"),
    path("dashboard/orders/", views.buyer_orders_list_view, name="buyer_orders"),
]
