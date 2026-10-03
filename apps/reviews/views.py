from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from apps.orders.models import Order
from .forms import ReviewForm
from .models import Review


@login_required
def create_review_view(request, order_number):
    """Permet à un acheteur de laisser un avis certifié sur une commande livrée ou payée."""
    order = get_object_or_404(
        Order.objects.select_related("campaign", "campaign__product", "campaign__product__store"),
        order_number=order_number,
    )

    if order.buyer != request.user and not getattr(request.user, "is_admin", False):
        raise PermissionDenied("Vous ne pouvez noter que vos propres commandes.")

    if hasattr(order, "review") and order.review is not None:
        messages.info(request, "Vous avez déjà déposé un avis sur cette commande.")
        return redirect("orders:detail", order_number=order.order_number)

    product = order.items.first().product if order.items.exists() else order.campaign.product
    store = product.store

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.order = order
            review.product = product
            review.store = store
            review.author = request.user
            review.is_verified_purchase = True
            review.is_approved = True
            review.save()

            # Mise à jour de la note moyenne de la boutique
            avg_rating = Review.objects.filter(store=store, is_approved=True).aggregate(avg=Avg("rating"))["avg"]
            if avg_rating is not None:
                store.rating_average = round(avg_rating, 2)
                store.save(update_fields=["rating_average"])

            messages.success(request, "Merci ! Votre avis vérifié a été enregistré avec succès.")
            return redirect("orders:detail", order_number=order.order_number)
    else:
        form = ReviewForm()

    return render(
        request,
        "reviews/review_form.html",
        {
            "order": order,
            "product": product,
            "store": store,
            "form": form,
        },
    )


def product_reviews_list_view(request, product_id):
    reviews = Review.objects.filter(product_id=product_id, is_approved=True).select_related("author").order_by("-created_at")
    return render(request, "reviews/review_list.html", {"reviews": reviews})
