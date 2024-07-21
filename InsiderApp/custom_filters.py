from django import template

register = template.Library()

@register.filter
def custom_intcomma(value):
    try:
        int_value = int(value)
        return "{:,}".format(int_value)
    except (ValueError, TypeError):
        return value
