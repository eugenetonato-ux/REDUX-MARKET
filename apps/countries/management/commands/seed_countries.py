from django.core.management.base import BaseCommand
from apps.countries.models import Country, Currency


class Command(BaseCommand):
    help = "Seed countries and currencies (Benin, Cote d'Ivoire, Senegal, Togo, etc.)"

    def handle(self, *args, **options):
        # 1. Currencies
        xof, _ = Currency.objects.get_or_create(
            code="XOF",
            defaults={"name": "Franc CFA BCEAO", "symbol": "CFA", "decimals": 0, "is_active": True},
        )
        eur, _ = Currency.objects.get_or_create(
            code="EUR",
            defaults={"name": "Euro", "symbol": "€", "decimals": 2, "is_active": True},
        )
        usd, _ = Currency.objects.get_or_create(
            code="USD",
            defaults={"name": "Dollar Américain", "symbol": "$", "decimals": 2, "is_active": True},
        )

        countries_data = [
            {"code": "BJ", "name": "Bénin", "phone_prefix": "+229", "currency": xof, "flag_emoji": "🇧🇯"},
            {"code": "CI", "name": "Côte d'Ivoire", "phone_prefix": "+225", "currency": xof, "flag_emoji": "🇨🇮"},
            {"code": "SN", "name": "Sénégal", "phone_prefix": "+221", "currency": xof, "flag_emoji": "🇸🇳"},
            {"code": "TG", "name": "Togo", "phone_prefix": "+228", "currency": xof, "flag_emoji": "🇹🇬"},
        ]

        for c_data in countries_data:
            country, created = Country.objects.get_or_create(
                code=c_data["code"],
                defaults=c_data,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Pays créé : {country.name} ({country.code})"))
            else:
                self.stdout.write(f"Pays existant : {country.name}")

        self.stdout.write(self.style.SUCCESS("Seeding des pays et devises terminé avec succès."))
