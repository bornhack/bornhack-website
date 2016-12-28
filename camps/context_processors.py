from django.conf import settings
from .models import Camp
from django.utils import timezone


def camp(request):
    if 'camp_slug' in request.resolver_match.kwargs:
        camp = Camp.objects.get(slug=request.resolver_match.kwargs['camp_slug'])
        request.session['campslug'] = camp.slug
    else:
        request.session['campslug'] = None
        camp = None

    return {
        'camps': Camp.objects.all().order_by('-camp_start'),
        'camp': camp
    }

