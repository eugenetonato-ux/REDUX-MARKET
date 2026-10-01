from django.utils.text import slugify
from apps.core.models import AuditLog
from .models import Store


def create_store(merchant, country, name, description="", phone="", email="", address="", city="", logo=None, banner=None):
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Store.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    store = Store.objects.create(
        merchant=merchant,
        country=country,
        name=name,
        slug=slug,
        description=description,
        phone=phone,
        email=email,
        address=address,
        city=city,
        logo=logo,
        banner=banner,
        is_active=True,
    )

    AuditLog.objects.create(
        actor=merchant.user,
        action="STORE_CREATED",
        content_object=store,
        changes={"name": name, "slug": slug, "country": country.code},
    )
    return store
