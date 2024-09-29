from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from jsonview.views import JsonView
from oauth2_provider.views.generic import ScopedProtectedResourceView

from .models import Profile


class ProfileDetail(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "profile_detail.html"
    active_menu = "profile"

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ["name", "description", "public_credit_name", "nickserv_username"]
    success_url = reverse_lazy("profiles:detail")
    template_name = "profile_form.html"

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

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


class ProfileApiView(JsonView, ScopedProtectedResourceView):
    required_scopes = ["profile:read"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = {
            "username": self.request.user.username,
            "user_id": self.request.user.id,
        }
        context["profile"] = {
            "public_credit_name": self.request.user.profile.get_public_credit_name,
            "description": self.request.user.profile.description,
        }
        context["teams"] = [
            {"team": team.name, "camp": team.camp.title}
            for team in self.request.user.teams.all()
        ]
        return context


class ProfilePermissionList(LoginRequiredMixin, ListView):
    model = Permission
    template_name = "permission_list.html"
    context_object_name = "permissions"

    def get_queryset(self, *args, **kwargs):
        perms = self.request.user.get_all_permissions()
        query = Q()
        for perm in perms:
            app_label, codename = perm.split(".")
            query |= Q(content_type__app_label=app_label, codename=codename)
        perms = (
            Permission.objects.filter(content_type__app_label="camps")
            .filter(query)
            .exclude(
                codename__in=["add_camp", "change_camp", "delete_camp", "view_camp"],
            )
        )
        return perms
