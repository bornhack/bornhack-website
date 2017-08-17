from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import Camp
from django.shortcuts import redirect
from .mixins import CampViewMixin
from django.views import View
from django.conf import settings
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class CampRedirectView(CampViewMixin, View):

    def dispatch(self, request, *args, **kwargs):
        # find the closest camp in the past
        prevcamp = Camp.objects.filter(
            camp__endswith__lt=timezone.now()
        ).order_by('-camp')[0]

        # find the closest upcoming camp
        nextcamp = Camp.objects.filter(
            camp__startswith__gt=timezone.now()
            ).order_by('camp')[0]

        # find the number of days between the two camps
        daysbetween = (nextcamp.camp.lower - prevcamp.camp.upper).days

        # find the number of days since the last camp ended
        dayssinceprevcamp = (timezone.now() - prevcamp.camp.lower).days

        # find the percentage of time passed
        percentpassed = (dayssinceprevcamp / daysbetween) * 100

        # do the redirect
        if percentpassed > settings.CAMP_REDIRECT_PERCENT:
            camp = nextcamp
        else:
            camp = prevcamp

        logger.debug("Redirecting to camp '%s' for page '%s' because %s%% of the time between the camps passed" % (camp.slug, kwargs['page'], int(percentpassed)))
        return redirect(kwargs['page'], camp_slug=camp.slug)


class CampDetailView(DetailView):
    model = Camp
    slug_url_kwarg = 'camp_slug'

    def get_template_names(self):
        return '%s_camp_detail.html' % self.get_object().slug


class CampListView(ListView):
    model = Camp
    template_name = 'camp_list.html'
    queryset = Camp.objects.all().order_by('camp')

