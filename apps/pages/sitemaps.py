from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from apps.campaigns.models import Campaign, CampaignStatus
from apps.purchase_requests.models import PurchaseRequest, RequestStatus
from apps.stores.models import Store


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "daily"

    def items(self):
        return [
            "pages:home",
            "pages:explorer",
            "pages:how_it_works",
            "pages:help",
            "pages:terms",
            "pages:privacy",
            "campaigns:list",
            "purchase_requests:list",
            "stores:list",
        ]

    def location(self, item):
        return reverse(item)


class CampaignSitemap(Sitemap):
    changefreq = "hourly"
    priority = 0.9

    def items(self):
        return Campaign.objects.filter(
            status__in=[CampaignStatus.ACTIVE, CampaignStatus.TARGET_REACHED]
        ).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("campaigns:detail", kwargs={"slug": obj.slug})


class StoreSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Store.objects.filter(is_active=True).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("stores:detail", kwargs={"slug": obj.slug})


class PurchaseRequestSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return PurchaseRequest.objects.filter(
            status__in=[RequestStatus.OPEN, RequestStatus.PROPOSALS_RECEIVED]
        ).order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("purchase_requests:detail", kwargs={"pk": obj.pk})
