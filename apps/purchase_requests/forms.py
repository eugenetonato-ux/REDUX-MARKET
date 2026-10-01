from datetime import timedelta
from decimal import Decimal
from django import forms
from django.utils import timezone
from apps.countries.models import Country
from apps.catalog.models import Category
from apps.stores.models import Store
from .models import PurchaseRequest, SellerProposal


class PurchaseRequestCreateForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        label="Titre de la demande",
        widget=forms.TextInput(attrs={"placeholder": "Ex: 50 sacs de riz parfumé 25kg"}),
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.filter(is_active=True),
        label="Pays de livraison souhaité",
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        label="Catégorie",
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Détails sur la qualité attendue, emballage, spécifications techniques..."}),
        label="Description du besoin",
    )
    target_quantity = forms.IntegerField(
        min_value=2,
        initial=10,
        label="Quantité totale ciblée (au moins 2)",
    )
    target_price = forms.DecimalField(
        min_value=Decimal("1"),
        decimal_places=2,
        label="Prix unitaire cible souhaité (FCFA)",
    )
    duration_days = forms.ChoiceField(
        choices=[
            ("7", "7 jours"),
            ("14", "14 jours"),
            ("30", "30 jours"),
        ],
        initial="14",
        label="Durée de la demande",
    )

    def clean_target_quantity(self):
        qty = self.cleaned_data.get("target_quantity")
        if qty < 2:
            raise forms.ValidationError("Une demande groupée doit regrouper au moins 2 unités.")
        return qty


class JoinPurchaseRequestForm(forms.Form):
    quantity_pledged = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Quantité que vous souhaitez commander",
    )


class SellerProposalForm(forms.Form):
    store = forms.ModelChoiceField(
        queryset=Store.objects.none(),
        label="Boutique émettrice",
    )
    proposed_price = forms.DecimalField(
        min_value=Decimal("1"),
        decimal_places=2,
        label="Prix unitaire proposé (FCFA)",
    )
    min_quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Quantité minimale pour activer ce prix",
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Modalités de livraison, garantie, marque proposée..."}),
        label="Précisions de votre offre",
    )
    validity_days = forms.ChoiceField(
        choices=[
            ("3", "3 jours"),
            ("7", "7 jours"),
            ("14", "14 jours"),
        ],
        initial="7",
        label="Validité de votre offre",
    )

    def __init__(self, *args, **kwargs):
        merchant = kwargs.pop("merchant", None)
        super().__init__(*args, **kwargs)
        if merchant:
            self.fields["store"].queryset = Store.objects.filter(merchant=merchant, is_active=True)
