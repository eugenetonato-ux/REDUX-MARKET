from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.i18n import set_language, JavaScriptCatalog
from apps.pages.sitemaps import CampaignSitemap, PurchaseRequestSitemap, StaticViewSitemap, StoreSitemap

sitemaps = {
    "static": StaticViewSitemap,
    "campaigns": CampaignSitemap,
    "stores": StoreSitemap,
    "requests": PurchaseRequestSitemap,
}

urlpatterns = [
    # Administration (URL secrète, non devinable)
    path(f"{settings.ADMIN_URL_PATH}/", admin.site.urls),

    # SEO Sitemaps
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    # i18n — Changement de langue (FR / EN)
    path("i18n/set-language/", set_language, name="set_language"),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),

    # API mobile-ready
    path("api/v1/", include("apps.api.v1.urls")),

    # Authentification
    path("", include("apps.accounts.urls")),

    # Pages publiques
    path("", include("apps.pages.urls")),
    path("products/", include("apps.catalog.urls")),
    path("stores/", include("apps.stores.urls")),
    path("campaigns/", include("apps.campaigns.urls")),
    path("requests/", include("apps.purchase_requests.urls")),

    # Tunnel de commande
    path("", include("apps.orders.urls")),
    path("", include("apps.payments.urls")),

    # Espaces connectés
    path("dashboard/", include("apps.accounts.urls_dashboard")),
    path("merchant/", include("apps.merchants.urls")),

    # Autres
    path("countries/", include("apps.countries.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("disputes/", include("apps.disputes.urls")),
    path("notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
