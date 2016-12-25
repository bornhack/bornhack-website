from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import *


class CampDetailView(DetailView):
    model = Camp
    template_name = 'camp_detail.html'
    slug_url_kwarg = 'camp_slug'

