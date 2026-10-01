from django.urls import path
from . import views

app_name = "purchase_requests"

urlpatterns = [
    path("", views.purchase_request_list, name="list"),
    path("nouveau/", views.purchase_request_create, name="create"),
    path("<int:pk>/", views.purchase_request_detail, name="detail"),
    path("<int:pk>/rejoindre/", views.purchase_request_join, name="join"),
    path("<int:pk>/proposer/", views.seller_proposal_create, name="proposal_create"),
    path("<int:pk>/propositions/<int:proposal_id>/accepter/", views.seller_proposal_accept, name="proposal_accept"),
]
