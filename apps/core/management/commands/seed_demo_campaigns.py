from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.services import get_or_create_demo_user
from apps.campaigns.models import Campaign, CampaignStatus, PricingPolicy
from apps.catalog.models import Category, Product
from apps.countries.models import Country, Currency
from apps.pricing.models import PriceTier
from apps.stores.models import Store


class Command(BaseCommand):
    help = "Initialise les comptes de test et des campagnes d'achats groupés réalistes avec paliers de prix"

    def handle(self, *args, **options):
        self.stdout.write("Génération des comptes de démonstration (Acheteur, Commerçant, Admin)...")
        buyer = get_or_create_demo_user("buyer")
        merchant_user = get_or_create_demo_user("merchant")
        admin_user = get_or_create_demo_user("admin")

        merchant_profile = merchant_user.merchant_profile
        store = merchant_profile.stores.first()

        currency = store.country.currency
        now = timezone.now()
        end_time = now + timedelta(days=14)

        # Catégories
        cat_mode, _ = Category.objects.get_or_create(name="Mode & Chaussures", defaults={"slug": "mode-chaussures", "is_active": True})
        cat_electro, _ = Category.objects.get_or_create(name="Électroménager", defaults={"slug": "electromenager", "is_active": True})
        cat_alimentaire, _ = Category.objects.get_or_create(name="Alimentation & Vivres", defaults={"slug": "alimentation", "is_active": True})
        cat_energie, _ = Category.objects.get_or_create(name="Énergie & Solaire", defaults={"slug": "energie-solaire", "is_active": True})

        campaigns_data = [
            {
                "prod_name": "Sneakers Streetwear Pro",
                "prod_slug": "sneakers-streetwear-pro",
                "category": cat_mode,
                "orig_price": Decimal("18000.00"),
                "camp_title": "Sneakers Streetwear Pro - Édition Urbaine",
                "camp_slug": "sneakers-streetwear-pro-edition-urbaine",
                "current_participants": 14,
                "target_participants": 20,
                "current_price": Decimal("12500.00"),
                "tiers": [
                    (1, 4, Decimal("18000.00"), Decimal("0.00")),
                    (5, 9, Decimal("15000.00"), Decimal("16.67")),
                    (10, 19, Decimal("12500.00"), Decimal("30.55")),
                    (20, None, Decimal("11000.00"), Decimal("38.89")),
                ],
            },
            {
                "prod_name": "Smart TV 43 Pouces Full HD Nasco",
                "prod_slug": "smart-tv-43-pouces-nasco",
                "category": cat_electro,
                "orig_price": Decimal("165000.00"),
                "camp_title": "Groupement Électro : Smart TV Nasco 43\"",
                "camp_slug": "groupement-electro-smart-tv-nasco-43",
                "current_participants": 7,
                "target_participants": 10,
                "current_price": Decimal("145000.00"),
                "tiers": [
                    (1, 4, Decimal("165000.00"), Decimal("0.00")),
                    (5, 9, Decimal("145000.00"), Decimal("12.12")),
                    (10, None, Decimal("130000.00"), Decimal("21.21")),
                ],
            },
            {
                "prod_name": "Sac de Riz Parfumé Royal 25kg",
                "prod_slug": "sac-de-riz-parfume-25kg",
                "category": cat_alimentaire,
                "orig_price": Decimal("24000.00"),
                "camp_title": "Achat Solidaire : Riz Parfumé Royal 25kg",
                "camp_slug": "achat-solidaire-riz-parfume-royal-25kg",
                "current_participants": 25,
                "target_participants": 25,
                "current_price": Decimal("18500.00"),
                "tiers": [
                    (1, 9, Decimal("24000.00"), Decimal("0.00")),
                    (10, 24, Decimal("21000.00"), Decimal("12.50")),
                    (25, None, Decimal("18500.00"), Decimal("22.91")),
                ],
            },
            {
                "prod_name": "Ventilateur Rechargeable Solaire 16\"",
                "prod_slug": "ventilateur-rechargeable-solaire-16",
                "category": cat_energie,
                "orig_price": Decimal("35000.00"),
                "camp_title": "Confort & Énergie : Ventilateur Solaire Anti-Coupure",
                "camp_slug": "ventilateur-solaire-anti-coupure",
                "current_participants": 9,
                "target_participants": 15,
                "current_price": Decimal("29500.00"),
                "tiers": [
                    (1, 4, Decimal("35000.00"), Decimal("0.00")),
                    (5, 14, Decimal("29500.00"), Decimal("15.71")),
                    (15, None, Decimal("26000.00"), Decimal("25.71")),
                ],
            },
        ]

        for item in campaigns_data:
            product, _ = Product.objects.get_or_create(
                slug=item["prod_slug"],
                defaults={
                    "store": store,
                    "category": item["category"],
                    "name": item["prod_name"],
                    "description": f"Produit officiel de haute qualité proposé à tarif dégressif collectif par {store.name}.",
                    "original_price": item["orig_price"],
                    "minimum_price": item["tiers"][-1][2],
                    "stock": 100,
                    "is_active": True,
                },
            )


            campaign, created = Campaign.objects.get_or_create(
                slug=item["camp_slug"],
                defaults={
                    "product": product,
                    "merchant": merchant_profile,
                    "creator": merchant_user,
                    "title": item["camp_title"],
                    "status": CampaignStatus.ACTIVE,
                    "pricing_policy": PricingPolicy.FINAL_TIER_PRICE,
                    "min_participants": 2,
                    "target_participants": item["target_participants"],
                    "current_participants_count": item["current_participants"],
                    "current_price": item["current_price"],
                    "start_date": now - timedelta(days=2),
                    "end_date": end_time,
                },
            )

            # Création des paliers si absents
            if not campaign.tiers.exists():
                for min_p, max_p, price, disc in item["tiers"]:
                    PriceTier.objects.create(
                        campaign=campaign,
                        min_participants=min_p,
                        max_participants=max_p,
                        price=price,
                        discount_percentage=disc,
                    )

        # 4. Demandes groupées inversées (Purchase Requests)
        from apps.purchase_requests.models import PurchaseRequest, RequestStatus, PurchaseRequestParticipant
        from apps.notifications.models import Notification
        from apps.orders.models import Order, OrderItem, OrderStatus
        from apps.reviews.models import Review

        pr, pr_created = PurchaseRequest.objects.get_or_create(
            title="Achat Groupé : Climatiseurs Inverter 1.5 CV",
            defaults={
                "creator": buyer,
                "country": store.country,
                "category": cat_electro,
                "description": "Nous cherchons à commander 15 climatiseurs solaires/inverter économiques pour résidences et bureaux à Cotonou.",
                "target_quantity": 15,
                "target_price": Decimal("180000.00"),
                "expires_at": now + timedelta(days=10),
                "status": RequestStatus.OPEN,
            },
        )
        if pr_created:
            PurchaseRequestParticipant.objects.create(
                purchase_request=pr,
                user=buyer,
                quantity_pledged=2,
            )

        # 5. Notifications pour l'acheteur démo
        Notification.objects.get_or_create(
            recipient=buyer,
            title="Bienvenue sur REDUX !",
            defaults={
                "message": "Profitez de remises dégressives inédites en rejoignant des achats groupés ou en créant vos demandes.",
                "link": "/campaigns/",
                "is_read": False,
            },
        )
        Notification.objects.get_or_create(
            recipient=buyer,
            title="Nouveau palier débloqué !",
            defaults={
                "message": "La campagne Sneakers Streetwear Pro vient d'atteindre le palier 3 (-30%). Votre prix baisse !",
                "link": "/campaigns/sneakers-streetwear-pro-edition-urbaine/",
                "is_read": False,
            },
        )

        # 6. Commande passée pour l'acheteur démo avec avis vérifié
        first_product = Product.objects.filter(store=store).first()
        if first_product:
            demo_order, ord_created = Order.objects.get_or_create(
                order_number="RDX-DEMO-2026-001",
                defaults={
                    "buyer": buyer,
                    "currency": currency,
                    "total_amount": Decimal("12500.00"),
                    "final_amount": Decimal("12500.00"),
                    "status": OrderStatus.DELIVERED,
                    "shipping_address": "Cotonou, Lot 142 Haie Vive, Rue 340",
                    "contact_phone": "+229 97 00 00 01",
                },
            )
            if ord_created:
                OrderItem.objects.create(
                    order=demo_order,
                    product=first_product,
                    quantity=1,
                    unit_price=Decimal("12500.00"),
                    total_price=Decimal("12500.00"),
                )
                Review.objects.get_or_create(
                    order=demo_order,
                    defaults={
                        "product": first_product,
                        "store": store,
                        "author": buyer,
                        "rating": 5,
                        "comment": "Commande reçue dans les délais à Cotonou ! Qualité irréprochable et vraie économie de groupe.",
                        "is_verified_purchase": True,
                        "is_approved": True,
                    },
                )
                # Mettre à jour la moyenne de la boutique
                store.rating_average = Decimal("5.00")
                store.save(update_fields=["rating_average"])

        self.stdout.write(self.style.SUCCESS("[OK] Donnees de demonstration, demandes groupees et commandes creees avec succes !"))
