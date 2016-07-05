from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import (
    Village,
)


class VillageListView(ListView):
    model = Village
    template_name = 'village_list.html'
    context_object_name = 'villages'


class VillageDetailView(DetailView):
    model = Village
    template_name = 'village_detail.html'
    context_object_name = 'village'


class VillageCreateView(CreateView):
    model = Village
    template_name = 'village_form.html'
    fields = ['name', 'description', 'private']
    success_url = reverse_lazy('villages:list')

    def form_valid(self, form):
        village = form.save(commit=False)
        village.contact = self.request.user
        village.save()
        return HttpResponseRedirect(village.get_absolute_url())


class VillageUpdateView(UpdateView):
    model = Village
    template_name = 'village_form.html'
    fields = ['name', 'description', 'private']

    def get_success_url(self):
        return self.get_object().get_absolute_url()
