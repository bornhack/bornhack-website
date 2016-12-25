from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import *


class CampInfoView(ListView):
    model = InfoCategory
    template_name = 'info.html'
    context_object_name = 'categories'

    def get_queryset(self, **kwargs):
        return InfoCategory.objects.filter(
            camp__slug=self.kwargs['camp_slug']
        )


