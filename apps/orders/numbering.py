import secrets
from django.utils import timezone


def generate_order_number():
    """
    Génère un numéro de commande unique et non prédictible de manière exploitable.
    Format : RDX-YYYYMM-XXXXXX (ex: RDX-202609-F83A2C)
    """
    from apps.orders.models import Order

    date_str = timezone.now().strftime("%Y%m")
    while True:
        token = secrets.token_hex(4).upper()  # 8 caractères hexadécimaux cryptographiquement aléatoires
        candidate = f"RDX-{date_str}-{token}"
        if not Order.objects.filter(order_number=candidate).exists():
            return candidate
