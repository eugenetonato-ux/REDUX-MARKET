from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        label="Note globale sur 5 étoiles",
        choices=[
            (5, "★★★★★ (5/5 - Excellent)"),
            (4, "★★★★☆ (4/5 - Très bien)"),
            (3, "★★★☆☆ (3/5 - Correct)"),
            (2, "★★☆☆☆ (2/5 - Décevant)"),
            (1, "★☆☆☆☆ (1/5 - Très décevant)"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 4,
                    "placeholder": "Partagez votre expérience sur la qualité du produit, la conformité de l'offre et la livraison...",
                }
            ),
        }
