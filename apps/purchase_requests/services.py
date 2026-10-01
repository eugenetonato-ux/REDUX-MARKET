from decimal import Decimal
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from apps.core.models import AuditLog
from .models import ProposalStatus, PurchaseRequest, PurchaseRequestParticipant, RequestStatus, SellerProposal


def create_purchase_request(creator, country, category, title, description, target_quantity, target_price, expires_at):
    if not creator or not creator.is_authenticated:
        raise PermissionDenied("Connexion requise pour créer une demande groupée.")

    target_quantity = int(target_quantity)
    target_price = Decimal(str(target_price))

    if target_quantity < 2:
        raise ValidationError("Une demande groupée doit viser au moins 2 unités.")

    if target_price <= Decimal("0"):
        raise ValidationError("Le prix cible doit être supérieur à 0.")

    if expires_at <= timezone.now():
        raise ValidationError("La date d'expiration doit être dans le futur.")

    req = PurchaseRequest.objects.create(
        creator=creator,
        country=country,
        category=category,
        title=title.strip(),
        description=description.strip(),
        target_quantity=target_quantity,
        target_price=target_price,
        status=RequestStatus.OPEN,
        expires_at=expires_at,
    )

    # Le créateur participe automatiquement avec 1 unité
    PurchaseRequestParticipant.objects.create(
        purchase_request=req,
        user=creator,
        quantity_pledged=1,
    )

    AuditLog.objects.create(
        actor=creator,
        action="PURCHASE_REQUEST_CREATED",
        content_object=req,
        changes={"title": title, "target_quantity": target_quantity, "target_price": str(target_price)},
    )
    return req


@transaction.atomic
def join_purchase_request(purchase_request, user, quantity_pledged=1):
    if not user or not user.is_authenticated:
        raise PermissionDenied("Connexion requise pour rejoindre cette demande.")

    if purchase_request.status != RequestStatus.OPEN:
        raise ValidationError(f"Cette demande n'accepte plus d'adhésions (Statut : {purchase_request.get_status_display()}).")

    if timezone.now() > purchase_request.expires_at:
        purchase_request.status = RequestStatus.EXPIRED
        purchase_request.save(update_fields=["status"])
        raise ValidationError("Cette demande groupée est expirée.")

    # Unicité de la participation (anti-doublon)
    if PurchaseRequestParticipant.objects.filter(purchase_request=purchase_request, user=user).exists():
        raise ValidationError("Vous participez déjà à cette demande groupée.")

    pledge = PurchaseRequestParticipant.objects.create(
        purchase_request=purchase_request,
        user=user,
        quantity_pledged=quantity_pledged,
    )

    AuditLog.objects.create(
        actor=user,
        action="PURCHASE_REQUEST_JOINED",
        content_object=pledge,
        changes={"quantity_pledged": quantity_pledged},
    )
    return pledge


def create_seller_proposal(purchase_request, merchant, store, proposed_price, min_quantity=1, description="", valid_until=None):
    # Règle de sécurité REDUX : Seuls les commerçants vérifiés peuvent soumettre une offre formelle
    if not merchant or not merchant.is_verified:
        raise PermissionDenied("Seuls les commerçants vérifiés par REDUX peuvent soumettre des propositions commerciales.")

    if purchase_request.status not in [RequestStatus.OPEN, RequestStatus.PROPOSALS_RECEIVED]:
        raise ValidationError("Cette demande ne reçoit plus de propositions.")

    proposed_price = Decimal(str(proposed_price))
    if proposed_price <= Decimal("0"):
        raise ValidationError("Le prix proposé doit être supérieur à 0.")

    if not valid_until:
        valid_until = purchase_request.expires_at

    proposal = SellerProposal.objects.create(
        purchase_request=purchase_request,
        merchant=merchant,
        store=store,
        proposed_price=proposed_price,
        min_quantity=min_quantity,
        description=description.strip(),
        status=ProposalStatus.PENDING,
        valid_until=valid_until,
    )

    # Passer le statut de la demande à PROPOSALS_RECEIVED
    if purchase_request.status == RequestStatus.OPEN:
        purchase_request.status = RequestStatus.PROPOSALS_RECEIVED
        purchase_request.save(update_fields=["status"])

    AuditLog.objects.create(
        actor=merchant.user,
        action="SELLER_PROPOSAL_CREATED",
        content_object=proposal,
        changes={"proposed_price": str(proposed_price), "merchant": merchant.business_name},
    )
    return proposal


@transaction.atomic
def accept_seller_proposal(purchase_request, proposal, user):
    # Seul le créateur ou un admin peut accepter une proposition
    if user != purchase_request.creator and not getattr(user, "is_admin", False):
        raise PermissionDenied("Seul l'initiateur de la demande peut sélectionner une offre.")

    if proposal.purchase_request_id != purchase_request.id:
        raise ValidationError("Cette offre ne correspond pas à la demande.")

    if timezone.now() > proposal.valid_until:
        proposal.status = ProposalStatus.EXPIRED
        proposal.save(update_fields=["status"])
        raise ValidationError("Cette offre commerçante a expiré.")

    # Accepter l'offre retenue
    proposal.status = ProposalStatus.ACCEPTED
    proposal.save(update_fields=["status"])

    # Rejeter les autres offres en attente
    purchase_request.proposals.exclude(id=proposal.id).filter(status=ProposalStatus.PENDING).update(
        status=ProposalStatus.REJECTED
    )

    purchase_request.status = RequestStatus.ACCEPTED
    purchase_request.save(update_fields=["status"])

    AuditLog.objects.create(
        actor=user,
        action="SELLER_PROPOSAL_ACCEPTED",
        content_object=proposal,
        changes={"accepted_proposal_id": proposal.id, "merchant": proposal.merchant.business_name},
    )
    return proposal
