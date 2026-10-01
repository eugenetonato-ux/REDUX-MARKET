from django.urls import path
from . import views

app_name = "campaigns"

urlpatterns = [
    path("", views.campaign_list_view, name="list"),
    path("<slug:slug>/", views.campaign_detail_view, name="detail"),
    path("<slug:slug>/join/", views.campaign_join_view, name="join"),
]
