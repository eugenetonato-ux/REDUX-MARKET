from decimal import Decimal, ROUND_HALF_UP


def calculate_current_tier(tiers, participant_count):
    if not tiers or participant_count <= 0:
        return None

    # Assure sorted by min_participants
    sorted_tiers = sorted(tiers, key=lambda t: t.min_participants)
    current = None

    for tier in sorted_tiers:
        if participant_count >= tier.min_participants:
            if tier.max_participants is None or participant_count <= tier.max_participants:
                current = tier
            elif participant_count > tier.max_participants:
                current = tier  # Fallback to current best tier until a higher tier is found

    return current


def calculate_current_price(tiers, participant_count, fallback_price):
    fallback_decimal = Decimal(str(fallback_price))
    tier = calculate_current_tier(tiers, participant_count)
    if tier:
        return Decimal(str(tier.price))
    return fallback_decimal


def get_next_tier(tiers, participant_count):
    if not tiers:
        return None

    sorted_tiers = sorted(tiers, key=lambda t: t.min_participants)
    for tier in sorted_tiers:
        if tier.min_participants > participant_count:
            return tier
    return None


def get_remaining_participants(tiers, participant_count):
    next_tier = get_next_tier(tiers, participant_count)
    if next_tier:
        return max(0, next_tier.min_participants - participant_count)
    return 0


def calculate_savings(original_price, current_price):
    orig = Decimal(str(original_price))
    curr = Decimal(str(current_price))

    if orig <= Decimal("0"):
        return Decimal("0.00"), Decimal("0.0")

    saved_amount = max(Decimal("0.00"), orig - curr)
    saved_percentage = (saved_amount / orig) * Decimal("100")
    saved_percentage = saved_percentage.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return saved_amount, saved_percentage
