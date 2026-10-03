from django.urls import path
from . import views

app_name = "disputes"

urlpatterns = [
    path("", views.dispute_list_view, name="list"),
    path("create/<str:order_number>/", views.dispute_create_view, name="create"),
    path("<int:pk>/", views.dispute_detail_view, name="detail"),
]
