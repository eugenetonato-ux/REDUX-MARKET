from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("create/<str:order_number>/", views.create_review_view, name="create"),
    path("product/<int:product_id>/", views.product_reviews_list_view, name="product_reviews"),
]
