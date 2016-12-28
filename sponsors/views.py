from django.views.generic import TemplateView
from camps.mixins import CampViewMixin


class SponsorIndexView(CampViewMixin, TemplateView):
    def get_template_name(self):
        return '%s-sponsors.html' % self.camp.slug


