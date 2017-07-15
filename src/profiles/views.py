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
    fields = ['name', 'description', 'public_credit_name']
    success_url = reverse_lazy('profiles:detail')
    template_name = 'profile_form.html'

    def get_object(self, queryset=None):
        return models.Profile.objects.get(user=self.request.user)

    def form_valid(self, form, **kwargs):
        if 'public_credit_name' in form.changed_data and form.cleaned_data['public_credit_name']:
            # user changed the name (to something non blank)
            form.instance.public_credit_name_approved = False
            form.instance.save()
        messages.info(self.request, 'Your profile has been updated.')
        return super().form_valid(form, **kwargs)

