"""
Formateurs monétaires pour REDUX — Afrique.
Fonctions utilitaires Python (non-template) pour formater les montants.
Utilisées dans les vues, les emails, les APIs, etc.
"""
import math
from decimal import Decimal, ROUND_DOWN


# Référentiel des devises africaines + internationales supportées
CURRENCY_CONFIG = {
    "XOF": {"symbol": "CFA",  "decimals": 0, "position": "after",  "name": "Franc CFA UEMOA"},
    "XAF": {"symbol": "FCFA", "decimals": 0, "position": "after",  "name": "Franc CFA CEMAC"},
    "NGN": {"symbol": "₦",    "decimals": 2, "position": "before", "name": "Naira nigérian"},
    "GHS": {"symbol": "₵",    "decimals": 2, "position": "before", "name": "Cedi ghanéen"},
    "GNF": {"symbol": "FG",   "decimals": 0, "position": "after",  "name": "Franc guinéen"},
    "CDF": {"symbol": "FC",   "decimals": 2, "position": "after",  "name": "Franc congolais"},
    "KES": {"symbol": "Ksh",  "decimals": 2, "position": "before", "name": "Shilling kényan"},
    "TZS": {"symbol": "TSh",  "decimals": 0, "position": "after",  "name": "Shilling tanzanien"},
    "ETB": {"symbol": "Br",   "decimals": 2, "position": "after",  "name": "Birr éthiopien"},
    "MAD": {"symbol": "DH",   "decimals": 2, "position": "after",  "name": "Dirham marocain"},
    "EGP": {"symbol": "E£",   "decimals": 2, "position": "before", "name": "Livre égyptienne"},
    "ZAR": {"symbol": "R",    "decimals": 2, "position": "before", "name": "Rand sud-africain"},
    "USD": {"symbol": "$",    "decimals": 2, "position": "before", "name": "Dollar américain"},
    "EUR": {"symbol": "€",    "decimals": 2, "position": "before", "name": "Euro"},
    "GBP": {"symbol": "£",    "decimals": 2, "position": "before", "name": "Livre sterling"},
}

# Séparateur millier : espace fine insécable (U+202F)
THOUSANDS_SEP = "\u202f"


def format_amount(amount, currency_code: str = "XOF") -> str:
    """
    Formate un montant numérique en chaîne localisée selon la devise.

    Examples:
        format_amount(5000, "XOF")   → "5 000 CFA"
        format_amount(99.99, "USD")  → "$ 99,99"
        format_amount(1500, "NGN")   → "₦ 1 500,00"
    """
    config = CURRENCY_CONFIG.get(currency_code.upper(), {
        "symbol": currency_code, "decimals": 2, "position": "after"
    })

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "—"

    decimals = config["decimals"]
    symbol = config["symbol"]
    position = config["position"]

    # Formate le montant
    if decimals == 0:
        int_part = int(round(amount))
        # Séparateur millier
        formatted = _format_integer(int_part)
    else:
        # Arrondir puis formater
        factor = 10 ** decimals
        rounded = math.floor(amount * factor) / factor
        int_part = int(rounded)
        frac_part = round((rounded - int_part) * factor)
        formatted = f"{_format_integer(int_part)},{str(frac_part).zfill(decimals)}"

    if position == "before":
        return f"{symbol}\u00a0{formatted}"
    else:
        return f"{formatted}\u00a0{symbol}"


def _format_integer(n: int) -> str:
    """Insère des espaces fines comme séparateur de milliers."""
    s = str(abs(n))
    parts = []
    while len(s) > 3:
        parts.append(s[-3:])
        s = s[:-3]
    parts.append(s)
    result = THOUSANDS_SEP.join(reversed(parts))
    return f"-{result}" if n < 0 else result


def calculate_discount_percent(original: float, current: float) -> int:
    """
    Calcule le pourcentage de réduction entre deux prix.
    Retourne un entier (planché, pas arrondi).
    """
    try:
        original = float(original)
        current = float(current)
        if original <= 0:
            return 0
        return math.floor(((original - current) / original) * 100)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


def get_currency_symbol(currency_code: str) -> str:
    """Retourne le symbole d'une devise."""
    return CURRENCY_CONFIG.get(currency_code.upper(), {}).get("symbol", currency_code)


def get_supported_currencies() -> list[dict]:
    """Retourne la liste des devises supportées avec leurs métadonnées."""
    return [
        {"code": code, **config}
        for code, config in CURRENCY_CONFIG.items()
    ]
