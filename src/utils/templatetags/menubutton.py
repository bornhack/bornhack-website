from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def menubuttonclass(context, appname):
    if appname == context['request'].resolver_match.func.view_class.__module__.split(".")[0]:
        return "btn-primary"
    else:
        return "btn-default"

