from decimal import Decimal
from django import forms
from django.utils import timezone
from apps.campaigns.models import Campaign, PricingPolicy
from apps.catalog.models import Category, Product
from apps.orders.models import OrderStatus
from apps.stores.models import Store


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "description",
            "original_price",
            "minimum_price",
            "stock",
            "unit",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: Smartphone Infinix Hot 40 Pro"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3, "placeholder": "Description détaillée du produit..."}),
            "original_price": forms.NumberInput(attrs={"class": "form-input", "placeholder": "Prix public unitaire (ex: 15000)"}),
            "minimum_price": forms.NumberInput(attrs={"class": "form-input", "placeholder": "Prix plancher minimum garanti (ex: 10000)"}),
            "stock": forms.NumberInput(attrs={"class": "form-input", "placeholder": "Quantité disponible"}),
            "unit": forms.TextInput(attrs={"class": "form-input", "placeholder": "pièce, carton, kg..."}),
        }

    def clean(self):
        cleaned_data = super().clean()
        orig = cleaned_data.get("original_price")
        mini = cleaned_data.get("minimum_price")
        if orig and mini and mini > orig:
            self.add_error("minimum_price", "Le prix minimum garanti ne peut pas être supérieur au prix d'origine.")
        return cleaned_data


class CampaignCreateForm(forms.Form):
    product = forms.ModelChoiceField(
        label="Produit concerné",
        queryset=Product.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    title = forms.CharField(
        label="Titre accrocheur de la campagne",
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: Achat Groupé : Smartphone Infinix Hot 40 Pro"}),
    )
    pricing_policy = forms.ChoiceField(
        label="Politique d'application du prix",
        choices=PricingPolicy.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    target_participants = forms.IntegerField(
        label="Objectif de participants (Palier max)",
        min_value=2,
        initial=20,
        widget=forms.NumberInput(attrs={"class": "form-input"}),
    )
    days_duration = forms.IntegerField(
        label="Durée de la campagne (en jours)",
        min_value=1,
        max_value=60,
        initial=14,
        widget=forms.NumberInput(attrs={"class": "form-input"}),
    )
    terms = forms.CharField(
        label="Conditions particulières (livraison, garantie)",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 2, "placeholder": "Garantie 12 mois, retrait immédiat en boutique..."}),
    )

    def __init__(self, *args, **kwargs):
        merchant = kwargs.pop("merchant", None)
        super().__init__(*args, **kwargs)
        if merchant:
            self.fields["product"].queryset = Product.objects.filter(store__merchant=merchant, is_active=True)


class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ["name", "description", "phone", "email", "address", "city"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "address": forms.TextInput(attrs={"class": "form-input"}),
            "city": forms.TextInput(attrs={"class": "form-input"}),
        }


class OrderStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        label="Nouveau statut de livraison",
        choices=[
            (OrderStatus.PROCESSING, "En préparation"),
            (OrderStatus.SHIPPED, "Expédiée (En cours de livraison)"),
            (OrderStatus.DELIVERED, "Livrée au client"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        label="Note ou numéro de suivi",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "ex: Colis remis au transporteur Express..."}),
    )
