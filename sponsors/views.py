from django.views.generic import TemplateView
from camps.mixins import CampViewMixin


class SponsorView(CampViewMixin, TemplateView):
    def get_template_names(self):
        return '%s-sponsors.html' % self.camp.slug


