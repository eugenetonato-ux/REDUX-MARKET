from django.core.management import call_command
from django.core.management.base import BaseCommand
from apps.countries.models import Country, Currency


class Command(BaseCommand):
    help = "Charge les devises et pays africains officiels depuis les fichiers JSON de fixtures"

    def handle(self, *args, **options):
        self.stdout.write("Chargement des devises et pays africains...")
        call_command("loaddata", "currencies", "countries")
        
        # S'assurer qu'aucun emoji ne persiste dans les drapeaux
        Country.objects.update(flag_emoji="")

        countries_count = Country.objects.count()
        currencies_count = Currency.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] {countries_count} pays africains et {currencies_count} devises chargés avec succès !"
            )
        )
