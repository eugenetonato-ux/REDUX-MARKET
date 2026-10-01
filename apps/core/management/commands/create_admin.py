from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.accounts.roles import UserRole


class Command(BaseCommand):
    help = "Création sécurisée d'un administrateur REDUX (rôle ADMIN non attribuable via l'interface)"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, required=True, help="Email de l'administrateur")
        parser.add_argument("--password", type=str, required=True, help="Mot de passe fort")
        parser.add_argument("--phone", type=str, required=False, default="", help="Numéro de téléphone")
        parser.add_argument("--name", type=str, required=False, default="Administrateur REDUX", help="Nom complet")

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        password = options["password"]
        phone = options.get("phone", "").strip() or None
        name = options.get("name", "Administrateur REDUX")

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"L'utilisateur {email} existe déjà."))
            return

        user = User.objects.create_superuser(
            email=email,
            password=password,
            phone=phone,
            full_name=name,
            role=UserRole.ADMIN,
        )
        self.stdout.write(self.style.SUCCESS(f"Administrateur créé avec succès : {user.email} (Rôle: {user.role})"))
