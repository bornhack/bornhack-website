from django import template

register = template.Library()


@register.filter
def currency(value):
    return "{0:.2f} DKK".format(value)


@register.filter(is_safe=True)
def truefalseicon(value):
    if value:
        return "<span class='text-success'>{% bootstrap_icon 'ok' %}</span>"
    else:
        return "<span class='text-danger'>{% bootstrap_icon 'remove' %}</span>"

