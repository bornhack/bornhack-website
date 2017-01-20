from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import *


class CampDetailView(DetailView):
    model = Camp
    slug_url_kwarg = 'camp_slug'

    def get_template_names(self):
        return 'camp_detail_%s.html' % self.get_object().slug

