from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("explorer/", views.explorer, name="explorer"),
    path("comment-ca-marche/", views.how_it_works, name="how_it_works"),
    path("aide/", views.help_view, name="help"),
    path("cgu/", views.terms_view, name="terms"),
    path("confidentialite/", views.privacy_view, name="privacy"),
    path("offline/", views.offline_view, name="offline"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
]
