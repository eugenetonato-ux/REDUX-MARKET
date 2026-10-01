from django.contrib import admin
from .models import PurchaseRequest, PurchaseRequestParticipant, SellerProposal


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "creator", "country", "target_quantity", "target_price", "status", "expires_at")
    list_filter = ("status", "country")


@admin.register(PurchaseRequestParticipant)
class PurchaseRequestParticipantAdmin(admin.ModelAdmin):
    list_display = ("purchase_request", "user", "quantity_pledged", "joined_at")


@admin.register(SellerProposal)
class SellerProposalAdmin(admin.ModelAdmin):
    list_display = ("purchase_request", "merchant", "proposed_price", "min_quantity", "status", "valid_until")
    list_filter = ("status",)
