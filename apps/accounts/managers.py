from django.contrib.auth.base_user import BaseUserManager
from django.core.exceptions import ValidationError
from .roles import UserRole


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email=None, phone=None, password=None, role=UserRole.BUYER, **extra_fields):
        if not email and not phone:
            raise ValueError("Un email ou un numéro de téléphone est obligatoire.")

        # Security check: public registrations cannot self-assign ADMIN
        if role == UserRole.ADMIN and not extra_fields.get("is_superuser"):
            raise ValidationError("Le rôle ADMIN ne peut pas être attribué automatiquement.")

        if email:
            email = self.normalize_email(email)

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, phone=phone, role=role, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superuser doit avoir is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)
