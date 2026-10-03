"""
Services de calcul et d'enregistrement des commissions plateforme REDUX.

Architecture :
  - resolve_commission_rule()  → trouve la règle la plus spécifique applicable
  - calculate_commission()     → calcul pur (taux + frais fixe) sans écriture BDD
  - record_commission()        → enregistre la PlatformTransaction post-paiement
  - get_commission_for_order() → sélecteur (lecture seule)

Point d'entrée depuis payments/services.py, appelé après la transition PAID.
"""
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from apps.core.models import AuditLog
from .models import CommissionRule, PlatformTransaction

# Taux par défaut si aucune règle configurée en base
DEFAULT_RATE_PERCENTAGE = Decimal("5.00")
DEFAULT_FIXED_FEE = Decimal("0.00")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Résolution de la règle de commission
# ─────────────────────────────────────────────────────────────────────────────

def resolve_commission_rule(order):
    """
    Trouve la CommissionRule la plus spécifique applicable à une commande.

    Priorité (du plus spécifique au plus général) :
      1. Pays + Catégorie correspondants
      2. Pays uniquement
      3. Catégorie uniquement
      4. Règle globale (country=None, category=None)

    Retourne None si aucune règle active n'est configurée (les valeurs par
    défaut seront alors utilisées).
    """
    now = timezone.now()

    # Extraire le pays et la catégorie depuis la commande
    country = None
    category = None

    try:
        if order.campaign and order.campaign.product:
            product = order.campaign.product
            category = product.category if hasattr(product, "category") else None
        if order.buyer:
            # Utilise le pays de l'acheteur via la session (stocké dans buyer.country si disponible)
            # Sinon on cherche via la campagne → boutique → pays
            if order.campaign and order.campaign.product and hasattr(order.campaign.product, "store"):
                store = order.campaign.product.store
                country = getattr(store, "country", None)
    except Exception:
        pass

    # Filtre de base : règles actives et dans la période de validité
    base_qs = CommissionRule.objects.filter(
        is_active=True,
    ).filter(
        # Validité temporelle : valid_from <= maintenant et (valid_until >= maintenant ou null)
        models_q(now)
    )

    # Priorité 1 : pays + catégorie
    if country and category:
        rule = base_qs.filter(country=country, category=category).first()
        if rule:
            return rule

    # Priorité 2 : pays uniquement
    if country:
        rule = base_qs.filter(country=country, category__isnull=True).first()
        if rule:
            return rule

    # Priorité 3 : catégorie uniquement
    if category:
        rule = base_qs.filter(country__isnull=True, category=category).first()
        if rule:
            return rule

    # Priorité 4 : règle globale
    rule = base_qs.filter(country__isnull=True, category__isnull=True).first()
    return rule


def models_q(now):
    """Helper interne : filtre de validité temporelle."""
    from django.db.models import Q
    return Q(valid_from__isnull=True) | Q(valid_from__lte=now), \
           Q(valid_until__isnull=True) | Q(valid_until__gte=now)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Calcul pur de la commission
# ─────────────────────────────────────────────────────────────────────────────

def calculate_commission(gross_amount: Decimal, rule: CommissionRule | None) -> dict:
    """
    Calcule la commission plateforme et le net reversé au commerçant.

    Args:
        gross_amount : Montant brut de la commande (final_amount)
        rule         : CommissionRule à appliquer (ou None → taux par défaut)

    Returns:
        dict avec :
          - rate_percentage  : taux appliqué (Decimal)
          - fixed_fee        : frais fixe appliqué (Decimal)
          - commission_amount: montant total prélevé par la plateforme (Decimal)
          - net_amount       : montant net reversé au commerçant (Decimal)
    """
    rate = rule.rate_percentage if rule else DEFAULT_RATE_PERCENTAGE
    fixed_fee = rule.fixed_fee if rule else DEFAULT_FIXED_FEE

    # Commission = (brut × taux%) + frais fixe
    commission = (gross_amount * rate / Decimal("100")) + fixed_fee
    commission = commission.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Garde-fou : la commission ne peut pas dépasser le montant brut
    commission = min(commission, gross_amount)

    net = gross_amount - commission
    net = net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "rate_percentage": rate,
        "fixed_fee": fixed_fee,
        "commission_amount": commission,
        "net_amount": net,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Enregistrement post-paiement (point d'entrée principal)
# ─────────────────────────────────────────────────────────────────────────────

@transaction.atomic
def record_commission(order, actor=None) -> PlatformTransaction | None:
    """
    Calcule et enregistre la commission plateforme après qu'une commande
    passe au statut PAID.

    - Idempotent : si une PlatformTransaction existe déjà pour cette commande,
      elle est retournée sans créer de doublon.
    - Résout automatiquement la règle de commission la plus spécifique.
    - Crée un AuditLog pour traçabilité.

    Args:
        order : Instance Order (status == PAID attendu)
        actor : Utilisateur déclencheur (None = système / webhook)

    Returns:
        PlatformTransaction créée ou existante, ou None en cas d'erreur.
    """
    # Idempotence : une seule commission par commande
    existing = PlatformTransaction.objects.filter(order=order).first()
    if existing:
        return existing

    gross_amount = order.final_amount

    if gross_amount <= 0:
        return None

    # Résolution de la règle
    rule = _resolve_rule_safe(order)

    # Calcul
    calc = calculate_commission(gross_amount, rule)

    # Enregistrement
    pt = PlatformTransaction.objects.create(
        order=order,
        commission_rule=rule,
        commission_rate=calc["rate_percentage"],
        commission_amount=calc["commission_amount"],
        gross_amount=gross_amount,
        net_merchant_amount=calc["net_amount"],
        status="COMPLETED",
    )

    AuditLog.objects.create(
        actor=actor,
        action="COMMISSION_RECORDED",
        content_object=pt,
        changes={
            "order_number": order.order_number,
            "gross_amount": str(gross_amount),
            "rate": str(calc["rate_percentage"]),
            "commission": str(calc["commission_amount"]),
            "net_merchant": str(calc["net_amount"]),
            "rule_id": rule.pk if rule else None,
        },
    )

    return pt


def _resolve_rule_safe(order) -> CommissionRule | None:
    """Appel sécurisé à resolve_commission_rule — ne lève jamais d'exception."""
    try:
        now = timezone.now()
        from django.db.models import Q

        base_qs = CommissionRule.objects.filter(
            is_active=True,
        ).filter(
            Q(valid_from__isnull=True) | Q(valid_from__lte=now)
        ).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=now)
        )

        country = None
        category = None

        try:
            if order.campaign and order.campaign.product:
                product = order.campaign.product
                category = getattr(product, "category", None)
                if hasattr(product, "store") and product.store:
                    country = getattr(product.store, "country", None)
        except Exception:
            pass

        # Priorité 1 : pays + catégorie
        if country and category:
            rule = base_qs.filter(country=country, category=category).first()
            if rule:
                return rule

        # Priorité 2 : pays
        if country:
            rule = base_qs.filter(country=country, category__isnull=True).first()
            if rule:
                return rule

        # Priorité 3 : catégorie
        if category:
            rule = base_qs.filter(country__isnull=True, category=category).first()
            if rule:
                return rule

        # Priorité 4 : globale
        return base_qs.filter(country__isnull=True, category__isnull=True).first()

    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Calculators (module calculators.py délégué ici pour clarté)
# ─────────────────────────────────────────────────────────────────────────────

def get_commission_for_order(order) -> PlatformTransaction | None:
    """
    Sélecteur : retourne la PlatformTransaction d'une commande ou None.
    Utilisé par le dashboard admin et le portail marchand.
    """
    return PlatformTransaction.objects.filter(order=order).select_related(
        "commission_rule", "order"
    ).first()


def get_commissions_summary(merchant=None, country=None, date_from=None, date_until=None) -> dict:
    """
    Calcule un résumé agrégé des commissions.
    Utilisé par le dashboard admin pour les KPIs.

    Returns:
        dict avec total_gross, total_commission, total_net, count
    """
    from django.db.models import Sum, Count

    qs = PlatformTransaction.objects.filter(status="COMPLETED")

    if merchant:
        qs = qs.filter(order__campaign__merchant=merchant)
    if country:
        qs = qs.filter(order__campaign__product__store__country=country)
    if date_from:
        qs = qs.filter(created_at__gte=date_from)
    if date_until:
        qs = qs.filter(created_at__lte=date_until)

    agg = qs.aggregate(
        total_gross=Sum("gross_amount"),
        total_commission=Sum("commission_amount"),
        total_net=Sum("net_merchant_amount"),
        count=Count("id"),
    )

    return {
        "total_gross": agg["total_gross"] or Decimal("0"),
        "total_commission": agg["total_commission"] or Decimal("0"),
        "total_net": agg["total_net"] or Decimal("0"),
        "count": agg["count"] or 0,
    }
