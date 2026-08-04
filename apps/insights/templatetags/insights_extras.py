from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """Dict lookup by variable key — Django templates don't support `dict[key]` directly."""
    return mapping.get(key)
