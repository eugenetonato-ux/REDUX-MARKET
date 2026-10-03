from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from apps.accounts.forms import (
    BuyerRegistrationForm,
    ForgotPasswordForm,
    LoginForm,
    MerchantRegistrationForm,
)
from apps.accounts.services import (
    get_or_create_demo_user,
    register_buyer,
    register_merchant,
)


def quick_login_view(request, role):
    """
    Connexion instantanée en 1 clic sans formulaire.
    Permet de tester et naviguer immédiatement dans les rôles :
    - 'buyer' : Acheteur
    - 'merchant' : Commerçant
    - 'admin' : Administrateur
    """
    role_key = role.strip().lower()
    allowed_roles = {
        "buyer": ("Acheteur", "/dashboard/"),
        "merchant": ("Commerçant", "/merchant/dashboard/"),
        "admin": ("Administrateur", f"/{settings.ADMIN_URL_PATH}/"),
    }

    if role_key not in allowed_roles:
        messages.error(request, f"Rôle '{role}' invalide pour la connexion express.")
        return redirect("accounts:login")

    role_label, target_url = allowed_roles[role_key]

    try:
        user = get_or_create_demo_user(role_key)
        login(request, user, backend="apps.accounts.backends.EmailOrPhoneBackend")
        messages.success(
            request,
            f"Connexion express réussie ! Vous êtes connecté en tant que {role_label} ({user.email})."
        )
        # Redirection vers la page demandée ou vers l'espace du rôle
        next_url = request.GET.get("next")
        return redirect(next_url or target_url)
    except Exception as e:
        messages.error(request, f"Erreur lors de la connexion express : {str(e)}")
        return redirect("accounts:login")


def login_view(request):
    """
    Page de connexion :
    - Propose des boutons d'accès direct 1-clic par rôle (Acheteur, Commerçant, Admin).
    - Propose également le formulaire de connexion classique (Email/Téléphone + Mot de passe).
    """
    if request.user.is_authenticated:
        if request.user.is_merchant:
            return redirect("merchants:dashboard")
        elif request.user.is_admin:
            return redirect(f"/{settings.ADMIN_URL_PATH}/")
        return redirect("dashboard:index")

    next_url = request.GET.get("next", "")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=identifier, password=password)
            if user:
                if not user.is_active:
                    messages.error(request, "Ce compte est actuellement désactivé. Veuillez contacter le support.")
                else:
                    login(request, user)
                    messages.success(request, f"Ravi de vous revoir, {user.full_name or user.email} !")

                    if next_url:
                        return redirect(next_url)
                    if user.is_merchant:
                        return redirect("merchants:dashboard")
                    elif user.is_admin:
                        return redirect(f"/{settings.ADMIN_URL_PATH}/")
                    return redirect("dashboard:index")
            else:
                messages.error(request, "Identifiant ou mot de passe incorrect. Vérifiez vos informations ou utilisez l'accès express.")
    else:
        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


def logout_view(request):
    """Déconnexion sécurisée de l'utilisateur."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "Vous avez été déconnecté avec succès. À très bientôt sur REDUX !")
    return redirect("pages:home")


def register_buyer_view(request):
    """Inscription pour les acheteurs."""
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        form = BuyerRegistrationForm(request.POST)
        if form.is_valid():
            user = register_buyer(
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                password=form.cleaned_data["password"],
                full_name=form.cleaned_data["full_name"],
                country=form.cleaned_data["country"],
                city=form.cleaned_data.get("city", ""),
            )
            login(request, user, backend="apps.accounts.backends.EmailOrPhoneBackend")
            messages.success(request, f"Bienvenue sur REDUX, {user.full_name} ! Votre compte Acheteur est prêt.")
            return redirect("dashboard:index")
    else:
        form = BuyerRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def register_merchant_view(request):
    """Inscription pour les commerçants."""
    if request.user.is_authenticated:
        if request.user.is_merchant:
            return redirect("merchants:dashboard")
        return redirect("dashboard:index")

    if request.method == "POST":
        form = MerchantRegistrationForm(request.POST)
        if form.is_valid():
            user = register_merchant(
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                password=form.cleaned_data["password"],
                full_name=form.cleaned_data["full_name"],
                business_name=form.cleaned_data["business_name"],
                country=form.cleaned_data["country"],
                business_type=form.cleaned_data.get("business_type", ""),
                city=form.cleaned_data.get("city", ""),
            )
            login(request, user, backend="apps.accounts.backends.EmailOrPhoneBackend")
            messages.success(
                request,
                f"Félicitations {user.full_name} ! Votre espace Commerçant et votre boutique ont été créés avec succès."
            )
            return redirect("merchants:dashboard")
    else:
        form = MerchantRegistrationForm()

    return render(request, "accounts/register_merchant.html", {"form": form})


def forgot_password_view(request):
    """Demande de réinitialisation de mot de passe."""
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            messages.success(
                request,
                "Si un compte correspond à cet identifiant, un lien de réinitialisation vous a été envoyé par SMS ou Email."
            )
            return redirect("accounts:login")
    else:
        form = ForgotPasswordForm()

    return render(request, "accounts/forgot_password.html", {"form": form})
