from django.urls import path
from . import views

app_name = "merchants"

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("products/", views.products_list_view, name="products"),
    path("products/create/", views.product_create_view, name="product_create"),
    path("campaigns/", views.campaigns_list_view, name="campaigns"),
    path("campaigns/create/", views.campaign_create_view, name="campaign_create"),
    path("campaigns/<int:campaign_id>/", views.merchant_campaign_detail_view, name="campaign_detail"),
    path("orders/", views.merchant_orders_view, name="orders"),
    path("orders/<str:order_number>/", views.merchant_order_detail_view, name="order_detail"),
    path("revenue/", views.revenue_view, name="revenue"),
    path("statistics/", views.statistics_view, name="statistics"),
    path("store/", views.store_settings_view, name="store"),
    path("verification/", views.verification_view, name="verification"),
]
