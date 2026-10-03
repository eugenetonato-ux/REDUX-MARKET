from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from apps.accounts.roles import UserRole


def role_required(allowed_roles):
    """
    Décorateur garantissant que l'utilisateur connecté possède l'un des rôles autorisés.
    En cas de rôle non autorisé, redirige élégamment avec un message clair.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.info(request, "Veuillez vous connecter pour accéder à cette page.")
                return redirect(f"/login/?next={request.path}")

            # Admin a toujours accès si spécifié ou via superuser
            if request.user.is_admin and (UserRole.ADMIN in allowed_roles or request.user.is_superuser):
                return view_func(request, *args, **kwargs)

            if request.user.role not in allowed_roles:
                if request.user.is_merchant:
                    messages.warning(request, "Cet espace est réservé aux acheteurs. Vous êtes actuellement sur votre compte Commerçant.")
                    return redirect("merchants:dashboard")
                elif request.user.is_buyer:
                    messages.warning(request, "Cet espace est réservé aux commerçants vérifiés. Accédez à votre espace acheteur ci-dessous.")
                    return redirect("dashboard:index")
                else:
                    messages.error(request, "Vous n'avez pas l'autorisation d'accéder à cette section.")
                    return redirect("pages:home")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def buyer_required(view_func):
    """Exige le rôle ACHETEUR."""
    return role_required([UserRole.BUYER])(view_func)


def merchant_required(view_func):
    """Exige le rôle COMMERÇANT."""
    return role_required([UserRole.MERCHANT])(view_func)


def admin_required(view_func):
    """Exige le rôle ADMINISTRATEUR."""
    return role_required([UserRole.ADMIN])(view_func)
