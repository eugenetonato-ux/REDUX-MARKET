from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Exécute tous les seeds initiaux (pays, devises, catégories)"

    def handle(self, *args, **options):
        self.stdout.write("Exécution de seed_countries...")
        call_command("seed_countries")
        self.stdout.write("Exécution de seed_categories...")
        call_command("seed_categories")
        self.stdout.write(self.style.SUCCESS("Tous les seeds initiaux ont été exécutés avec succès !"))
