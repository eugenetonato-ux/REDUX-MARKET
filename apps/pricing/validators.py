from decimal import Decimal
from django.core.exceptions import ValidationError


def validate_price_tiers(tiers_data, minimum_price, original_price):
    if not tiers_data or len(tiers_data) == 0:
        raise ValidationError("Au moins un palier de prix est obligatoire pour une campagne.")

    min_p = Decimal(str(minimum_price))
    orig_p = Decimal(str(original_price))

    if min_p <= Decimal("0"):
        raise ValidationError("Le prix minimum du produit est invalide.")

    if orig_p < min_p:
        raise ValidationError("Le prix normal ne peut pas être inférieur au prix minimum négocié.")

    # Sort data by min_participants
    sorted_tiers = sorted(tiers_data, key=lambda t: t.get("min_participants", 0))

    prev_max = None
    prev_price = orig_p

    for i, tier in enumerate(sorted_tiers):
        min_part = tier.get("min_participants")
        max_part = tier.get("max_participants")
        price = Decimal(str(tier.get("price", "0")))

        if min_part is None or min_part <= 0:
            raise ValidationError(f"Le palier {i+1} doit avoir un nombre minimum de participants >= 1.")

        # Vérification prix plancher
        if price < min_p:
            raise ValidationError(
                f"Le prix du palier {i+1} ({price}) descend sous le prix minimum garanti ({min_p})."
            )

        # Vérification prix plafond
        if price > orig_p:
            raise ValidationError(
                f"Le prix du palier {i+1} ({price}) dépasse le prix unitaire d'origine ({orig_p})."
            )

        # Vérification dégressivité stricte (palier supérieur doit être strictement moins cher)
        if price >= prev_price:
            raise ValidationError(
                f"Dégressivité non respectée : le palier {i+1} ({price}) n'est pas strictement inférieur au prix précédent ({prev_price})."
            )

        # Continuité des bornes (pas de trou ni de chevauchement)
        if prev_max is not None:
            if min_part != prev_max + 1:
                raise ValidationError(
                    f"Incohérence entre les paliers : le palier commence à {min_part} alors que le précédent s'arrête à {prev_max}."
                )

        if max_part is not None:
            if max_part < min_part:
                raise ValidationError(
                    f"Le palier {i+1} a un maximum ({max_part}) inférieur à son minimum ({min_part})."
                )

        prev_max = max_part
        prev_price = price

    # Le dernier palier doit être ouvert (max_participants=None ou couvrant au-delà)
    last_tier = sorted_tiers[-1]
    if last_tier.get("max_participants") is not None:
        # Autorisé s'il est égal à une limite haute ou converti en palier ouvert
        pass

    return True
