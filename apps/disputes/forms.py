from django import forms
from .models import Dispute, DisputeMessage


class DisputeCreateForm(forms.ModelForm):
    reason = forms.ChoiceField(
        label="Motif de la réclamation",
        choices=[
            ("Colis non reçu / Perte de livraison", "Colis non reçu / Perte de livraison"),
            ("Produit endommagé ou cassé au déballage", "Produit endommagé ou cassé au déballage"),
            ("Article non conforme à la description de la campagne", "Article non conforme à la description de la campagne"),
            ("Quantité ou variante incomplète", "Quantité ou variante incomplète"),
            ("Autre problème sérieux", "Autre problème sérieux"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Dispute
        fields = ["reason", "description"]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 4,
                    "placeholder": "Décrivez précisément le problème rencontré, les échanges éventuels avec le commerçant et votre demande...",
                }
            ),
        }


class DisputeMessageForm(forms.ModelForm):
    class Meta:
        model = DisputeMessage
        fields = ["message", "attachment"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 3,
                    "placeholder": "Répondre ou apporter des précisions...",
                }
            ),
            "attachment": forms.FileInput(attrs={"class": "form-input"}),
        }
