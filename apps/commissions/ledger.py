"""
Ledger (grand livre) des commissions REDUX.
Fournit des exports et des rapports comptables agrégés par période.
Utilisé par l'administration pour la réconciliation financière.
"""
from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import PlatformTransaction


def get_monthly_ledger(year: int, month: int, merchant=None) -> dict:
    """
    Rapport mensuel des commissions.

    Args:
        year     : Année (ex: 2026)
        month    : Mois (1-12)
        merchant : Filtrer par commerçant (optionnel)

    Returns:
        dict avec totaux brut, commission, net + nombre de transactions
    """
    from django.db.models import Q
    import calendar

    _, last_day = calendar.monthrange(year, month)
    date_from = timezone.datetime(year, month, 1, tzinfo=timezone.utc)
    date_until = timezone.datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    qs = PlatformTransaction.objects.filter(
        status="COMPLETED",
        created_at__gte=date_from,
        created_at__lte=date_until,
    )
    if merchant:
        qs = qs.filter(order__campaign__merchant=merchant)

    agg = qs.aggregate(
        total_gross=Sum("gross_amount"),
        total_commission=Sum("commission_amount"),
        total_net=Sum("net_merchant_amount"),
        avg_rate=Avg("commission_rate"),
        count=Count("id"),
    )

    return {
        "period": f"{year}-{month:02d}",
        "total_gross": agg["total_gross"] or Decimal("0"),
        "total_commission": agg["total_commission"] or Decimal("0"),
        "total_net": agg["total_net"] or Decimal("0"),
        "avg_rate": agg["avg_rate"] or Decimal("0"),
        "transaction_count": agg["count"] or 0,
    }


def get_daily_ledger(days: int = 30, merchant=None) -> list[dict]:
    """
    Rapport jour par jour sur les N derniers jours.

    Returns:
        Liste de dict {date, gross, commission, net, count} triée par date ASC
    """
    from django.db.models.functions import TruncDate

    date_from = timezone.now() - timedelta(days=days)
    qs = PlatformTransaction.objects.filter(
        status="COMPLETED",
        created_at__gte=date_from,
    )
    if merchant:
        qs = qs.filter(order__campaign__merchant=merchant)

    rows = (
        qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            gross=Sum("gross_amount"),
            commission=Sum("commission_amount"),
            net=Sum("net_merchant_amount"),
            count=Count("id"),
        )
        .order_by("day")
    )

    return [
        {
            "date": str(r["day"]),
            "gross": r["gross"] or Decimal("0"),
            "commission": r["commission"] or Decimal("0"),
            "net": r["net"] or Decimal("0"),
            "count": r["count"],
        }
        for r in rows
    ]


def get_top_merchants_by_volume(limit: int = 10, days: int = 30) -> list[dict]:
    """
    Classement des commerçants par volume de commissions sur les N derniers jours.

    Returns:
        Liste de dict {merchant_name, total_gross, total_commission, order_count}
    """
    date_from = timezone.now() - timedelta(days=days)

    rows = (
        PlatformTransaction.objects.filter(
            status="COMPLETED",
            created_at__gte=date_from,
        )
        .values("order__campaign__merchant__business_name")
        .annotate(
            total_gross=Sum("gross_amount"),
            total_commission=Sum("commission_amount"),
            order_count=Count("id"),
        )
        .order_by("-total_gross")[:limit]
    )

    return [
        {
            "merchant_name": r["order__campaign__merchant__business_name"] or "—",
            "total_gross": r["total_gross"] or Decimal("0"),
            "total_commission": r["total_commission"] or Decimal("0"),
            "order_count": r["order_count"],
        }
        for r in rows
    ]
