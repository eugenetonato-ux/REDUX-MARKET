from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from apps.core.models import AuditLog
from .models import Category, Product, ProductImage, ProductVariant


def create_product(store, name, original_price, minimum_price, stock=0, category=None, description="", unit="pièce", is_featured=False, user=None):
    original_price = Decimal(str(original_price))
    minimum_price = Decimal(str(minimum_price))

    if minimum_price <= Decimal("0"):
        raise ValidationError("Le prix minimum doit être strictement supérieur à 0.")

    if original_price < minimum_price:
        raise ValidationError("Le prix normal ne peut pas être inférieur au prix minimum négocié.")

    if stock < 0:
        raise ValidationError("Le stock ne peut pas être négatif.")

    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    product = Product.objects.create(
        store=store,
        category=category,
        name=name,
        slug=slug,
        description=description,
        original_price=original_price,
        minimum_price=minimum_price,
        stock=stock,
        unit=unit,
        is_active=True,
        is_featured=is_featured,
    )

    AuditLog.objects.create(
        actor=user or store.merchant.user,
        action="PRODUCT_CREATED",
        content_object=product,
        changes={
            "name": name,
            "original_price": str(original_price),
            "minimum_price": str(minimum_price),
            "stock": stock,
        },
    )
    return product


def add_product_image(product, image, is_primary=False, order=0):
    if is_primary:
        # Reset other primary images
        product.images.filter(is_primary=True).update(is_primary=False)

    return ProductImage.objects.create(
        product=product,
        image=image,
        is_primary=is_primary,
        order=order,
    )
