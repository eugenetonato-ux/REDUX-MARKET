from decimal import Decimal
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from apps.core.models import AuditLog
from apps.pricing.calculators import calculate_current_price
from apps.pricing.services import create_price_tiers_for_campaign
from .models import Campaign, CampaignParticipant, CampaignParticipantStatus, CampaignStatus, PricingPolicy
from .state_machine import transition_campaign_status


def create_campaign(
    product,
    creator,
    merchant,
    title,
    target_participants,
    min_participants,
    max_participants,
    start_date,
    end_date,
    tiers_data,
    pricing_policy=PricingPolicy.CURRENT_TIER_PRICE,
    terms="",
):
    if not product.is_active:
        raise ValidationError("Le produit sélectionné n'est pas actif.")

    if product.stock <= 0:
        raise ValidationError("Le produit n'a aucun stock disponible.")

    if end_date <= start_date:
        raise ValidationError("La date de fin doit être postérieure à la date de début.")

    if min_participants < 2:
        raise ValidationError("Une campagne collective doit requérir au minimum 2 participants.")

    if target_participants < min_participants:
        raise ValidationError("L'objectif visé ne peut pas être inférieur au minimum de participants.")

    if max_participants and max_participants < target_participants:
        raise ValidationError("Le plafond maximum ne peut pas être inférieur à l'objectif visé.")

    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while Campaign.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Statut : si le commerçant est vérifié, la campagne peut être ACTIVE directement, sinon PENDING_APPROVAL
    initial_status = CampaignStatus.ACTIVE if merchant.is_verified else CampaignStatus.PENDING_APPROVAL

    campaign = Campaign.objects.create(
        product=product,
        merchant=merchant,
        creator=creator,
        title=title,
        slug=slug,
        status=initial_status,
        pricing_policy=pricing_policy,
        target_participants=target_participants,
        min_participants=min_participants,
        max_participants=max_participants,
        current_participants_count=0,
        current_price=product.original_price,
        start_date=start_date,
        end_date=end_date,
        terms=terms,
    )

    # Configurer les paliers de prix
    create_price_tiers_for_campaign(campaign, tiers_data, user=creator)

    AuditLog.objects.create(
        actor=creator,
        action="CAMPAIGN_CREATED",
        content_object=campaign,
        changes={"title": title, "slug": slug, "status": initial_status},
    )
    return campaign


@transaction.atomic
def join_campaign(campaign, user, quantity=1):
    if not user or not user.is_authenticated:
        raise PermissionDenied("Vous devez être connecté pour participer à une campagne.")

    # Recharger avec verrouillage pour éviter toute concurrence sur les compteurs
    campaign = Campaign.objects.select_for_update().get(pk=campaign.pk)

    if campaign.status != CampaignStatus.ACTIVE:
        raise ValidationError(f"Cette campagne n'accepte plus de participations (Statut: {campaign.get_status_display()}).")

    if timezone.now() > campaign.end_date:
        transition_campaign_status(campaign, CampaignStatus.EXPIRED, actor=user)
        raise ValidationError("Cette campagne est expirée.")

    # Anti-abus : Vérifier qu'une participation active n'existe pas déjà pour cet utilisateur
    existing = CampaignParticipant.objects.filter(
        campaign=campaign,
        user=user,
        status=CampaignParticipantStatus.JOINED,
    ).exists()
    if existing:
        raise ValidationError("Vous participez déjà activement à cette campagne collective.")

    # Vérification plafond max_participants
    new_count = campaign.current_participants_count + quantity
    if campaign.max_participants and new_count > campaign.max_participants:
        raise ValidationError(
            f"Le nombre maximum de participants ({campaign.max_participants}) serait dépassé."
        )

    # Calculer le prix unitaire appliqué selon les paliers de la campagne
    tiers = list(campaign.tiers.all().order_by("min_participants"))
    unit_price = calculate_current_price(
        tiers=tiers,
        participant_count=new_count,
        fallback_price=campaign.product.original_price,
    )
    total_amount = unit_price * Decimal(str(quantity))

    participant = CampaignParticipant.objects.create(
        campaign=campaign,
        user=user,
        quantity=quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        status=CampaignParticipantStatus.JOINED,
    )

    # Mettre à jour la campagne
    campaign.current_participants_count = new_count
    campaign.current_price = unit_price

    # Si l'objectif est atteint
    if new_count >= campaign.target_participants and campaign.status == CampaignStatus.ACTIVE:
        transition_campaign_status(campaign, CampaignStatus.TARGET_REACHED, actor=user)

    campaign.save(update_fields=["current_participants_count", "current_price"])

    AuditLog.objects.create(
        actor=user,
        action="CAMPAIGN_JOINED",
        content_object=participant,
        changes={
            "quantity": quantity,
            "unit_price": str(unit_price),
            "total_amount": str(total_amount),
            "new_campaign_participants_count": new_count,
        },
    )
    return participant
