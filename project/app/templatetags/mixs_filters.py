from django import template
from ..mixs_metadata_standards import MIXS_METADATA_STANDARDS

register = template.Library()

@register.filter
def get_mixs_standard_display(value):
    return dict(MIXS_METADATA_STANDARDS).get(value, value)


@register.filter
def get_mixs_standard_key(value):
    return next((item[0] for item in MIXS_METADATA_STANDARDS if item[1] == value), value)