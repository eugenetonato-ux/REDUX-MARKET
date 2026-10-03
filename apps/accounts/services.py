import logging
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.accounts.models import BuyerProfile
from apps.accounts.roles import UserRole
from apps.countries.models import Country, Currency
from apps.merchants.models import MerchantProfile, VerificationStatus
from apps.stores.models import Store

logger = logging.getLogger(__name__)
User = get_user_model()


def get_or_create_default_country():
    """Récupère ou initialise un pays et une devise par défaut pour les démos et nouveaux comptes."""
    currency, _ = Currency.objects.get_or_create(
        code="XOF",
        defaults={
            "name": "Franc CFA",
            "symbol": "FCFA",
            "decimals": 0,
            "is_active": True,
        },
    )
    country, _ = Country.objects.get_or_create(
        code="BJ",
        defaults={
            "name": "Bénin",
            "phone_prefix": "+229",
            "currency": currency,
            "is_active": True,
            "flag_emoji": "",
        },
    )
    return country


@transaction.atomic
def register_buyer(email=None, phone=None, password=None, full_name="", country=None, city="", shipping_address=""):
    """Crée un nouvel utilisateur avec le rôle ACHETEUR et son profil associé."""
    if not country:
        country = get_or_create_default_country()

    email_val = email.strip().lower() if email else None
    phone_val = phone.strip() if phone else None

    user = User(
        email=email_val,
        phone=phone_val,
        full_name=full_name.strip(),
        role=UserRole.BUYER,
        country=country,
        email_verified=True,
    )
    if password:
        user.set_password(password)
    else:
        user.set_unusable_password()
    user.save()

    BuyerProfile.objects.create(
        user=user,
        city=city.strip(),
        default_shipping_address=shipping_address.strip(),
    )
    return user


@transaction.atomic
def register_merchant(
    email=None,
    phone=None,
    password=None,
    full_name="",
    business_name="",
    country=None,
    business_type="Commerce Général",
    city="",
):
    """Crée un nouvel utilisateur avec le rôle COMMERÇANT, son profil marchand et sa boutique initiale."""
    if not country:
        country = get_or_create_default_country()

    email_val = email.strip().lower() if email else None
    phone_val = phone.strip() if phone else None
    biz_name = business_name.strip() if business_name else f"Boutique {full_name.strip()}"

    user = User(
        email=email_val,
        phone=phone_val,
        full_name=full_name.strip(),
        role=UserRole.MERCHANT,
        country=country,
        email_verified=True,
    )
    if password:
        user.set_password(password)
    else:
        user.set_unusable_password()
    user.save()

    merchant_profile = MerchantProfile.objects.create(
        user=user,
        business_name=biz_name,
        business_type=business_type,
        verification_status=VerificationStatus.VERIFIED,
        is_active=True,
    )

    # Création automatique de la boutique par défaut
    import re
    from django.utils.text import slugify

    base_slug = slugify(biz_name) or f"store-{user.id}"
    slug = base_slug
    counter = 1
    while Store.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    Store.objects.create(
        merchant=merchant_profile,
        country=country,
        name=biz_name,
        slug=slug,
        description=f"Bienvenue chez {biz_name}. Retrouvez nos meilleures offres collectives !",
        phone=phone_val or "",
        email=email_val or "",
        city=city or "Cotonou",
        is_active=True,
        rating_average=4.9,
    )

    return user


@transaction.atomic
def get_or_create_demo_user(role_type: str):
    """
    Permet une connexion express sans formulaire pour le développement et la démo.
    Crée automatiquement le compte avec toutes ses liaisons si inexistant.
    Rôles acceptés: 'buyer', 'merchant', 'admin'
    """
    country = get_or_create_default_country()
    role_type = role_type.lower()

    if role_type == "buyer":
        email = "client@redux.app"
        user = User.objects.filter(email=email).first()
        if not user:
            user = User(
                email=email,
                phone="+22997223344",
                full_name="Koffi Mensah (Acheteur Démo)",
                role=UserRole.BUYER,
                country=country,
                is_active=True,
                email_verified=True,
            )
            user.set_password("Redux2026!Demo")
            user.save()

        # Profil acheteur
        BuyerProfile.objects.get_or_create(
            user=user,
            defaults={
                "city": "Cotonou",
                "default_shipping_address": "Haie Vive, Rue 340, Cotonou, Bénin",
            },
        )
        return user

    elif role_type == "merchant":
        email = "boutique@redux.app"
        user = User.objects.filter(email=email).first()
        if not user:
            user = User(
                email=email,
                phone="+22997112233",
                full_name="Aminata Diallo (Commerçante Démo)",
                role=UserRole.MERCHANT,
                country=country,
                is_active=True,
                email_verified=True,
            )
            user.set_password("Redux2026!Demo")
            user.save()

        # Profil commerçant
        merchant_profile, _ = MerchantProfile.objects.get_or_create(
            user=user,
            defaults={
                "business_name": "AfroTech & Lifestyle",
                "business_type": "Électronique & Mode",
                "verification_status": VerificationStatus.VERIFIED,
                "is_active": True,
            },
        )

        # Boutique associée
        if not merchant_profile.stores.exists():
            Store.objects.create(
                merchant=merchant_profile,
                country=country,
                name="AfroTech Store",
                slug="afrotech-store",
                description="Boutique certifiée de produits high-tech et accessoires de qualité à prix de groupe.",
                phone=user.phone or "+22997112233",
                email=email,
                city="Cotonou",
                is_active=True,
                rating_average=4.95,
            )
        return user

    elif role_type == "admin":
        email = "admin@redux.app"
        user = User.objects.filter(email=email).first()
        if not user:
            user = User(
                email=email,
                phone="+22997000000",
                full_name="Administrateur REDUX",
                role=UserRole.ADMIN,
                country=country,
                is_active=True,
                is_staff=True,
                is_superuser=True,
                email_verified=True,
            )
            user.set_password("Redux2026!Admin")
            user.save()
        else:
            if not user.is_staff or not user.is_superuser:
                user.is_staff = True
                user.is_superuser = True
                user.role = UserRole.ADMIN
                user.save(update_fields=["is_staff", "is_superuser", "role"])
        return user

    raise ValueError(f"Rôle inconnu pour la connexion express : {role_type}")
