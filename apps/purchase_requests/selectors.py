from django.db.models import Count, Sum
from django.utils import timezone
from .models import PurchaseRequest, PurchaseRequestParticipant, RequestStatus, SellerProposal


def get_active_purchase_requests(country_code=None, category_id=None):
    """
    Retourne les demandes d'achat groupé ouvertes ou ayant reçu des propositions,
    non expirées, annotées du nombre de participants et volume engagé.
    """
    qs = (
        PurchaseRequest.objects.filter(
            status__in=[RequestStatus.OPEN, RequestStatus.PROPOSALS_RECEIVED],
            expires_at__gt=timezone.now(),
        )
        .select_related("country", "category", "creator")
        .annotate(
            total_participants=Count("participants", distinct=True),
            total_pledged=Sum("participants__quantity_pledged"),
        )
        .order_by("-created_at")
    )

    if country_code:
        qs = qs.filter(country__code=country_code.upper())
    if category_id:
        qs = qs.filter(category_id=category_id)

    return qs


def get_purchase_request_detail(request_id):
    """
    Récupère le détail d'une demande avec ses participants et propositions.
    """
    return (
        PurchaseRequest.objects.filter(id=request_id)
        .select_related("country", "category", "creator")
        .prefetch_related(
            "participants__user",
            "proposals__merchant__user",
            "proposals__store",
        )
        .annotate(
            total_participants=Count("participants", distinct=True),
            total_pledged=Sum("participants__quantity_pledged"),
        )
        .first()
    )


def get_user_pledged_requests(user):
    """
    Retourne les demandes auxquelles l'utilisateur participe.
    """
    if not user or not user.is_authenticated:
        return PurchaseRequest.objects.none()
    return (
        PurchaseRequest.objects.filter(participants__user=user)
        .select_related("country", "category", "creator")
        .distinct()
        .order_by("-created_at")
    )


def get_user_created_requests(user):
    """
    Retourne les demandes initiées par l'utilisateur.
    """
    if not user or not user.is_authenticated:
        return PurchaseRequest.objects.none()
    return (
        PurchaseRequest.objects.filter(creator=user)
        .select_related("country", "category")
        .order_by("-created_at")
    )
