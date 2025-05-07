from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import FormView
from django.views.generic import UpdateView
from jsonview.views import JsonView
from oauth2_provider.views.generic import ScopedProtectedResourceView
from leaflet.forms.widgets import LeafletWidget

from .models import Profile
from .forms import OIDCForm
from bornhack.oauth_validators import BornhackOAuth2Validator


class ProfileDetail(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "profile_detail.html"
    active_menu = "profile"

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = [
        "name",
        "description",
        "public_credit_name",
        "phonenumber",
        "location",
        "nickserv_username",
        "theme",
        "preferred_username",
    ]
    success_url = reverse_lazy("profiles:detail")
    template_name = "profile_form.html"

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "class": "form-control",
            },
        )
        return form

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
        """Get real Permission objects so we have the perm descriptions as well."""
        query = Q()
        # loop over users permissions and build an OR query
        for perm in self.request.user.get_all_permissions():
            app_label, codename = perm.split(".")
            query |= Q(content_type__app_label=app_label, codename=codename)
        # get and return the objects
        perms = (
            Permission.objects.none()
            .filter(query)
            .exclude(
                codename__in=["add_camp", "change_camp", "delete_camp", "view_camp"],
            )
        )
        return perms


class ProfileOIDCView(LoginRequiredMixin, FormView):
    template_name = "oidc.html"
    form_class = OIDCForm

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        validator = BornhackOAuth2Validator()
        self.scopes = validator.oidc_claim_scope
        self.claims = validator.get_additional_claims(request=self.request)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
            scopes = self.request.GET.getlist(key="scopes")
            self.initial["scopes"] = scopes
        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["claims"] = {}
        for claim, value in self.claims.items():
            scope = self.scopes[claim]
            if scope in self.request.GET.getlist(key="scopes"):
                context["claims"][claim] = value
        context["scopes"] = self.scopes
        context["active_scopes"] = ["openid"] + sorted(
            set(self.request.GET.getlist(key="scopes")),
        )
        context["all_scopes"] = sorted(set(self.scopes.values()))
        del context["all_scopes"][context["all_scopes"].index("openid")]
        return context
