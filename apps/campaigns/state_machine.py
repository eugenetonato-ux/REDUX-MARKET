from django.core.exceptions import ValidationError
from apps.core.models import AuditLog
from .models import CampaignStatus


VALID_TRANSITIONS = {
    CampaignStatus.DRAFT: [CampaignStatus.PENDING_APPROVAL, CampaignStatus.ACTIVE, CampaignStatus.CANCELLED],
    CampaignStatus.PENDING_APPROVAL: [CampaignStatus.ACTIVE, CampaignStatus.REJECTED if hasattr(CampaignStatus, 'REJECTED') else CampaignStatus.FAILED, CampaignStatus.CANCELLED],
    CampaignStatus.ACTIVE: [CampaignStatus.TARGET_REACHED, CampaignStatus.PAYMENT_PENDING, CampaignStatus.EXPIRED, CampaignStatus.CANCELLED, CampaignStatus.SUSPENDED],
    CampaignStatus.TARGET_REACHED: [CampaignStatus.PAYMENT_PENDING, CampaignStatus.SUCCESS, CampaignStatus.CANCELLED, CampaignStatus.SUSPENDED],
    CampaignStatus.PAYMENT_PENDING: [CampaignStatus.SUCCESS, CampaignStatus.FAILED, CampaignStatus.SUSPENDED],
    CampaignStatus.SUCCESS: [],
    CampaignStatus.FAILED: [],
    CampaignStatus.EXPIRED: [],
    CampaignStatus.CANCELLED: [],
    CampaignStatus.SUSPENDED: [CampaignStatus.ACTIVE, CampaignStatus.CANCELLED],
}


def transition_campaign_status(campaign, new_status, actor=None, reason=""):
    current = campaign.status
    if current == new_status:
        return campaign

    allowed = VALID_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Transition de statut interdite : impossible de passer de '{current}' à '{new_status}'."
        )

    campaign.status = new_status
    campaign.save(update_fields=["status"])

    AuditLog.objects.create(
        actor=actor or campaign.merchant.user,
        action="CAMPAIGN_STATUS_TRANSITION",
        content_object=campaign,
        changes={"old_status": current, "new_status": new_status, "reason": reason},
    )
    return campaign
