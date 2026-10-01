from rest_framework import permissions
from apps.accounts.roles import UserRole


class IsMerchantUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == UserRole.MERCHANT or request.user.is_superuser)
        )


class IsVerifiedMerchant(IsMerchantUser):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.user.is_superuser:
            return True
        profile = getattr(request.user, "merchant_profile", None)
        return bool(profile and profile.is_verified)
