from django.views.generic import TemplateView
from camps.mixins import CampViewMixin


class SponsorsView(CampViewMixin, TemplateView):
    def get_template_names(self):
        return '%s-sponsors.html' % self.camp.slug


class CallForSponsorsView(CampViewMixin, TemplateView):
    def get_template_names(self):
        return '%s-call-for-sponsors.html' % self.camp.slug


