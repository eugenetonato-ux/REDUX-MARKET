"""
Template tags pour le formatage monétaire multi-devises de REDUX.
Usage : {% load money %}
        {{ price|currency:request.country }}
        {{ price|currency_code:"XOF" }}
        {% format_price price country %}
"""
from django import template
from django.utils.safestring import mark_safe
import math

register = template.Library()


def _format_amount(amount, decimals=0, symbol="", code="", position="after"):
    """Formate un montant selon les conventions de la devise."""
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return f"{symbol} —" if position == "before" else f"— {symbol}"

    if decimals == 0:
        # Devises sans centimes (XOF, XAF, GNF, etc.)
        formatted = f"{amount:,.0f}".replace(",", "\u202f")  # espace fine
    else:
        formatted = f"{amount:,.{decimals}f}".replace(",", "\u202f").replace(".", ",")

    if position == "before":
        return f"{symbol}\u00a0{formatted}"
    else:
        return f"{formatted}\u00a0{symbol}"


# Mapping code devise → position du symbole
_SYMBOL_POSITION = {
    "USD": "before",
    "EUR": "before",
    "GBP": "before",
}


@register.filter(name="currency")
def currency_filter(amount, country=None):
    """
    Formate un prix en fonction du pays actif (objet Country avec .currency).
    Usage : {{ product.price|currency:request.country }}
    """
    if country is None or not hasattr(country, "currency"):
        # Fallback : format brut XOF
        try:
            return f"{float(amount):,.0f}\u00a0XOF".replace(",", "\u202f")
        except (TypeError, ValueError):
            return "—"

    cur = country.currency
    symbol = cur.symbol or cur.code
    decimals = cur.decimals if cur.decimals is not None else 0
    position = _SYMBOL_POSITION.get(cur.code, "after")

    return mark_safe(_format_amount(amount, decimals, symbol, cur.code, position))


@register.filter(name="currency_code")
def currency_code_filter(amount, code="XOF"):
    """
    Formate un prix avec un code devise explicite.
    Usage : {{ product.price|currency_code:"XOF" }}
    """
    # Symboles hardcodés pour les devises africaines principales
    CURRENCY_MAP = {
        "XOF": {"symbol": "CFA", "decimals": 0, "position": "after"},
        "XAF": {"symbol": "FCFA", "decimals": 0, "position": "after"},
        "NGN": {"symbol": "₦", "decimals": 2, "position": "before"},
        "GHS": {"symbol": "₵", "decimals": 2, "position": "before"},
        "GNF": {"symbol": "FG", "decimals": 0, "position": "after"},
        "CDF": {"symbol": "FC", "decimals": 2, "position": "after"},
        "USD": {"symbol": "$", "decimals": 2, "position": "before"},
        "EUR": {"symbol": "€", "decimals": 2, "position": "before"},
        "GBP": {"symbol": "£", "decimals": 2, "position": "before"},
    }
    info = CURRENCY_MAP.get(code.upper(), {"symbol": code, "decimals": 2, "position": "after"})
    return mark_safe(_format_amount(amount, info["decimals"], info["symbol"], code, info["position"]))


@register.simple_tag(takes_context=True)
def format_price(context, amount, label="", css_class=""):
    """
    Tag de formatage complet avec contexte pays automatique.
    Usage : {% format_price product.price %}
            {% format_price product.price label="Prix palier" css_class="text-green-600" %}
    Returns HTML safe string.
    """
    request = context.get("request")
    country = getattr(request, "country", None) if request else None

    formatted = currency_filter(amount, country)

    if label:
        html = (
            f'<span class="price-wrapper {css_class}">'
            f'<span class="price-label">{label}</span> '
            f'<span class="price-amount">{formatted}</span>'
            f"</span>"
        )
    else:
        html = f'<span class="price-amount {css_class}">{formatted}</span>'

    return mark_safe(html)


@register.filter(name="percent_off")
def percent_off(original, current):
    """
    Calcule le % de réduction entre deux prix.
    Usage : {{ original_price|percent_off:current_price }}
    """
    try:
        original = float(original)
        current = float(current)
        if original <= 0:
            return 0
        discount = ((original - current) / original) * 100
        return math.floor(discount)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


@register.inclusion_tag("partials/price.html", takes_context=True)
def price_display(context, amount, original_amount=None, label=""):
    """
    Tag d'inclusion pour afficher un prix avec badge de réduction optionnel.
    Usage : {% price_display product.price product.original_price %}
    """
    request = context.get("request")
    country = getattr(request, "country", None) if request else None

    discount = 0
    if original_amount:
        discount = percent_off(original_amount, amount)

    return {
        "amount": currency_filter(amount, country),
        "original_amount": currency_filter(original_amount, country) if original_amount else None,
        "discount": discount,
        "label": label,
        "country": country,
    }
