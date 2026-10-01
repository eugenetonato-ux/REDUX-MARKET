from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.catalog.models import Category


class Command(BaseCommand):
    help = "Seed initial product categories"

    def handle(self, *args, **options):
        categories_tree = [
            {
                "name": "Électronique & High-Tech",
                "icon": "smartphone",
                "children": ["Smartphones & Tablettes", "Ordinateurs & Accessoires", "Téléviseurs & Audio"],
            },
            {
                "name": "Mode & Habillement",
                "icon": "shirt",
                "children": ["Hommes", "Femmes", "Enfants", "Chaussures & Maroquinerie"],
            },
            {
                "name": "Maison & Électroménager",
                "icon": "home",
                "children": ["Cuisine & Électroménager", "Mobilier & Décoration", "Literie"],
            },
            {
                "name": "Alimentation & Épicerie",
                "icon": "shopping-cart",
                "children": ["Boissons & Jus", "Épicerie salée & sucrée", "Produits du terroir"],
            },
            {
                "name": "Beauté & Santé",
                "icon": "sparkles",
                "children": ["Soins du visage & corps", "Parfums", "Bien-être"],
            },
        ]

        order = 1
        for parent_data in categories_tree:
            parent_slug = slugify(parent_data["name"])
            parent, created = Category.objects.get_or_create(
                slug=parent_slug,
                defaults={
                    "name": parent_data["name"],
                    "icon": parent_data.get("icon", ""),
                    "display_order": order,
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Catégorie parent créée : {parent.name}"))
            order += 1

            sub_order = 1
            for child_name in parent_data.get("children", []):
                child_slug = slugify(f"{parent_slug}-{child_name}")
                child, c_created = Category.objects.get_or_create(
                    slug=child_slug,
                    defaults={
                        "name": child_name,
                        "parent": parent,
                        "display_order": sub_order,
                        "is_active": True,
                    },
                )
                if c_created:
                    self.stdout.write(f"  -> Sous-categorie creee : {child.name}")
                sub_order += 1

        self.stdout.write(self.style.SUCCESS("Seeding des catégories terminé."))
