from django.views.generic import TemplateView, ListView
from camps.mixins import CampViewMixin

from .models import Sponsor


class SponsorsView(CampViewMixin, ListView):
    model = Sponsor
    template_name = 'sponsors.html'
    context_object_name = 'sponsors'

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()
        return queryset.filter(tier__camp=self.camp).order_by('tier__weight')


class CallForSponsorsView(CampViewMixin, TemplateView):
    def get_template_names(self):
        return '%s_call_for_sponsors.html' % self.camp.slug
