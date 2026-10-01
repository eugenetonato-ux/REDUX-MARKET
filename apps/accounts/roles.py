from django.db import models


class UserRole(models.TextChoices):
    BUYER = "BUYER", "Acheteur"
    MERCHANT = "MERCHANT", "Commerçant"
    ADMIN = "ADMIN", "Administrateur"
