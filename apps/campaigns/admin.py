from django.contrib import admin
from .models import Campaign, CampaignParticipant, CampaignStatus, CampaignView


@admin.action(description="✓ Approuver et activer les campagnes sélectionnées")
def approve_selected_campaigns(modeladmin, request, queryset):
    updated = queryset.filter(status=CampaignStatus.PENDING_APPROVAL).update(
        status=CampaignStatus.ACTIVE
    )
    modeladmin.message_user(request, f"{updated} campagne(s) approuvée(s) et publiée(s) avec succès.")


class CampaignParticipantInline(admin.TabularInline):
    model = CampaignParticipant
    extra = 0
    readonly_fields = ("joined_at", "total_amount")


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "merchant", "status", "current_price", "current_participants_count", "end_date")
    list_filter = ("status", "pricing_policy")
    search_fields = ("title", "product__name", "merchant__business_name")
    prepopulated_fields = {"slug": ("title",)}
    actions = [approve_selected_campaigns]
    inlines = [CampaignParticipantInline]


@admin.register(CampaignParticipant)
class CampaignParticipantAdmin(admin.ModelAdmin):
    list_display = ("campaign", "user", "quantity", "unit_price", "total_amount", "status", "joined_at")
    list_filter = ("status",)
    search_fields = ("campaign__title", "user__email", "user__phone")
