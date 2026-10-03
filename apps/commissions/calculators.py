"""
Calculators de commission — fonctions pures réutilisables.
Délèguent à commissions/services.py pour la logique métier.
"""
from decimal import Decimal
from .services import calculate_commission, get_commissions_summary  # noqa: F401 (ré-export)


def estimate_commission(gross_amount: Decimal, rate_percentage: Decimal = Decimal("5.00"),
                         fixed_fee: Decimal = Decimal("0.00")) -> dict:
    """
    Estimation rapide sans résolution de règle BDD.
    Utilisée pour afficher une estimation côté front (ex: page checkout).

    Returns:
        dict avec commission_amount et net_amount
    """
    from decimal import ROUND_HALF_UP

    commission = (gross_amount * rate_percentage / Decimal("100")) + fixed_fee
    commission = commission.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    commission = min(commission, gross_amount)

    return {
        "rate_percentage": rate_percentage,
        "fixed_fee": fixed_fee,
        "commission_amount": commission,
        "net_amount": (gross_amount - commission).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }
