from django.urls import path
from . import views

app_name = "countries"

urlpatterns = [
    path("change/", views.change_country, name="change"),
]
