from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from . import models


class ProfileDetail(LoginRequiredMixin, DetailView):
    model = models.Profile
    template_name = 'profile_detail.html'

    def get_object(self, queryset=None):
        return models.Profile.objects.get(user=self.request.user)


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = models.Profile
    fields = ['name', 'description']
    success_url = reverse_lazy('profiles:detail')
    template_name = 'profile_form.html'

    def get_object(self, queryset=None):
        return models.Profile.objects.get(user=self.request.user)

    def form_valid(self, form, **kwargs):
        messages.info(self.request, 'Your profile has been updated.')
        return super(ProfileUpdate, self).form_valid(form, **kwargs)

