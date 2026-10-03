from django import forms
from django.contrib.auth import get_user_model
from apps.countries.models import Country

User = get_user_model()


class LoginForm(forms.Form):
    identifier = forms.CharField(
        label="Email ou Numéro de téléphone",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "ex: nom@domaine.com ou +22997000000",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        ),
    )


class BuyerRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label="Nom complet",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: Koffi Mensah"}),
    )
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "koffi@exemple.com"}),
    )
    phone = forms.CharField(
        label="Numéro de téléphone",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: +229 97 00 00 00"}),
    )
    country = forms.ModelChoiceField(
        label="Pays",
        queryset=Country.objects.filter(is_active=True),
        empty_label="Sélectionnez votre pays",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    city = forms.CharField(
        label="Ville",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: Cotonou"}),
    )
    password = forms.CharField(
        label="Mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Au moins 8 caractères"}),
    )
    confirm_password = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Retapez le mot de passe"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte avec cette adresse email existe déjà.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Un compte avec ce numéro de téléphone existe déjà.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Les deux mots de passe ne correspondent pas.")
        return cleaned_data


class MerchantRegistrationForm(forms.Form):
    full_name = forms.CharField(
        label="Nom du responsable",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: Aminata Diallo"}),
    )
    business_name = forms.CharField(
        label="Nom de l'entreprise ou boutique",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: Tech & Style Cotonou"}),
    )
    business_type = forms.CharField(
        label="Secteur d'activité",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: High-Tech, Mode, Électroménager"}),
    )
    email = forms.EmailField(
        label="Email professionnel",
        widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "contact@maboutique.com"}),
    )
    phone = forms.CharField(
        label="Téléphone commercial / WhatsApp",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: +229 97 11 22 33"}),
    )
    country = forms.ModelChoiceField(
        label="Pays d'opération",
        queryset=Country.objects.filter(is_active=True),
        empty_label="Sélectionnez votre pays",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    city = forms.CharField(
        label="Ville principale",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: Cotonou"}),
    )
    password = forms.CharField(
        label="Mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Au moins 8 caractères"}),
    )
    confirm_password = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Retapez le mot de passe"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte avec cet email existe déjà.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Un compte avec ce numéro existe déjà.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Les mots de passe ne sont pas identiques.")
        return cleaned_data


class ForgotPasswordForm(forms.Form):
    identifier = forms.CharField(
        label="Votre Email ou Téléphone",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Entrez votre email ou numéro",
                "autocomplete": "username",
            }
        ),
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["full_name", "email", "phone"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "readonly": "readonly"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
        }
