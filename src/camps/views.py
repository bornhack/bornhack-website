import logging

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView
from django.views.generic import ListView

from .models import Camp

logger = logging.getLogger("bornhack.%s" % __name__)


class CampRedirectView(View):
    def dispatch(self, request, *args, **kwargs):
        now = timezone.now()

        try:
            camp = Camp.objects.get(camp__contains=now)
            logger.debug(
                "Redirecting to camp '%s' for page '%s' because it is now!" % (camp.slug, kwargs["page"]),
            )
            return redirect(kwargs["page"], camp_slug=camp.slug)
        except Camp.DoesNotExist:
            pass

        # no ongoing camp, find the closest camp in the past
        try:
            prevcamp = Camp.objects.filter(camp__endswith__lt=now).order_by("-camp").first()
        except Camp.DoesNotExist:
            prevcamp = None

        # find the closest upcoming camp
        try:
            nextcamp = Camp.objects.filter(camp__startswith__gt=now).order_by("camp").first()
        except Camp.DoesNotExist:
            nextcamp = None

        percentpassed = False
        if prevcamp and nextcamp:
            # find the number of days between the two camps
            daysbetween = (nextcamp.camp.lower - prevcamp.camp.upper).days

            # find the number of days since the last camp ended
            dayssinceprevcamp = (timezone.now() - prevcamp.camp.lower).days

            # find the percentage of time passed
            percentpassed = (dayssinceprevcamp / daysbetween) * 100

        # figure out where to redirect
        if percentpassed > settings.CAMP_REDIRECT_PERCENT or not prevcamp:
            # either we have no previous camp, or we have both and more than settings.CAMP_REDIRECT_PERCENT has passed, so redirect to the next camp
            camp = nextcamp
        else:
            # either we have no next camp, or we have both and less than settings.CAMP_REDIRECT_PERCENT has passed, so redirect to the previous camp
            camp = prevcamp

        # do the redirect
        return redirect(kwargs["page"], camp_slug=camp.slug)


class CampDetailView(DetailView):
    model = Camp
    slug_url_kwarg = "camp_slug"

    def get_template_names(self):
        return "%s_camp_detail.html" % self.get_object().slug


class CampListView(ListView):
    model = Camp
    template_name = "camp_list.html"
    queryset = Camp.objects.all().order_by("camp")
