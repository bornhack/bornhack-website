from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages


from . import models, forms


class ProfileDetail(LoginRequiredMixin, DetailView):
    model = models.Profile

    def get_object(self, queryset=None):
        return models.Profile.objects.get(user=self.request.user)


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = models.Profile
    form_class = forms.ProfileForm
    success_url = reverse_lazy('profiles:detail')

    def get_object(self, queryset=None):
        return models.Profile.objects.get(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super(ProfileUpdate, self).get_form_kwargs()
        kwargs['initial'] = {'email': self.object.user.email}
        return kwargs

    def form_valid(self, form, **kwargs):
        self.object.user.email = form.cleaned_data['email']
        self.object.user.save()
        messages.info(self.request, 'Your profile has been updated.')
        return super(ProfileUpdate, self).form_valid(form, **kwargs)
