from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import *


class CampDetailView(DetailView):
    model = Camp
    slug_url_kwarg = 'camp_slug'

    def get_template_names(self):
        return '%s_camp_detail.html' % self.get_object().slug


class CampListView(ListView):
    model = Camp
    template_name = 'camp_list.html'

