from django import template
from apps.core.admin_dashboard import get_platform_metrics

register = template.Library()


@register.simple_tag
def platform_metrics():
    return get_platform_metrics()
