from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_buyer_view, name="register"),
    path("register/merchant/", views.register_merchant_view, name="register_merchant"),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("quick-login/<str:role>/", views.quick_login_view, name="quick_login"),
]
