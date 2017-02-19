from django.conf import settings
from .models import Camp
from django.utils import timezone


def camp(request):
    """
    if we have a camp_slug url component then get the "current" Camp object.
    Return it after adding the slug to request.session along with a "camps"
    queryset containing all camps (used to build the menu and such)
    """
    if request.resolver_match and 'camp_slug' in request.resolver_match.kwargs:
        try:
            camp = Camp.objects.get(slug=request.resolver_match.kwargs['camp_slug'])
            request.session['campslug'] = camp.slug
        except Camp.DoesNotExist:
            request.session['campslug'] = None
            camp = None
    else:
        request.session['campslug'] = None
        camp = None

    return {
        'camps': Camp.objects.all().order_by('-camp'),
        'camp': camp
    }

