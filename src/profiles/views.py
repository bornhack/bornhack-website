from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic import UpdateView
from jsonview.views import JsonView
from oauth2_provider.views.generic import ProtectedResourceView

from . import models


class ProfileDetail(LoginRequiredMixin, DetailView):
    model = models.Profile
    template_name = "profile_detail.html"
    active_menu = "profile"

    def get_object(self, queryset=None):
        return models.Profile.objects.get(user=self.request.user)


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = models.Profile
    fields = ["name", "description", "public_credit_name", "nickserv_username"]
    success_url = reverse_lazy("profiles:detail")
    template_name = "profile_form.html"

    def get_object(self, queryset=None):
        return models.Profile.objects.get(user=self.request.user)

    def form_valid(self, form, **kwargs):
        if (
            "public_credit_name" in form.changed_data
            and form.cleaned_data["public_credit_name"]
        ):
            # user changed the name (to something non blank)
            form.instance.public_credit_name_approved = False
            form.instance.save()
        messages.success(self.request, "Your profile has been updated.")
        return super().form_valid(form, **kwargs)


class ProfileApiView(JsonView, ProtectedResourceView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = {"username": self.request.user.username}
        context["profile"] = {
            "public_credit_name": self.request.user.profile.get_public_credit_name,
            "description": self.request.user.profile.description,
        }
        context["teams"] = [
            {"team": team.name, "camp": team.camp.title}
            for team in self.request.user.teams.all()
        ]
        return context
