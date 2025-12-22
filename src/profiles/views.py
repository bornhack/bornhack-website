"""Views for the user profile pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import UpdateView
from jsonview.views import JsonView
from oauth2_provider.views.generic import ScopedProtectedResourceView

from bornhack.oauth_validators import BornhackOAuth2Validator
from facilities.models import FacilityFeedback

if TYPE_CHECKING:
    from typing import ClassVar

    from django.db.models import QuerySet
    from django.forms import BaseForm
    from django.forms import Form

from .forms import OIDCForm
from .models import Profile


class ProfileDetail(LoginRequiredMixin, DetailView):
    """User profile details view."""

    model = Profile
    template_name = "profile_detail.html"
    active_menu = "profile"

    def get_object(self, queryset: QuerySet = None) -> QuerySet:
        """Method for fetching user profile."""
        return Profile.objects.get(user=self.request.user)


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    """View for updating the user profile."""

    model = Profile
    fields: ClassVar[list[str]] = [
        "name",
        "description",
        "public_credit_name",
        "phonenumber",
        "nickserv_username",
        "theme",
        "preferred_username",
    ]
    success_url = reverse_lazy("profiles:detail")
    template_name = "profile_form.html"

    def get_object(self, queryset: QuerySet = None) -> QuerySet:
        """Method for fetching user profile."""
        return Profile.objects.get(user=self.request.user)

    def form_valid(self, form: BaseForm, **kwargs) -> HttpResponse:
        """Check form valid."""
        if "public_credit_name" in form.changed_data and form.cleaned_data["public_credit_name"]:
            # user changed the name (to something non blank)
            form.instance.public_credit_name_approved = False
            form.instance.save()
        if "theme" in form.changed_data and form.cleaned_data["theme"]:
            self.request.session["theme"] = form.cleaned_data["theme"]
        messages.success(self.request, "Your profile has been updated.")
        return super().form_valid(form, **kwargs)


class ProfileApiView(JsonView, ScopedProtectedResourceView):
    """View for showing user profile in json."""

    required_scopes: ClassVar[list[str]] = ["profile:read"]

    def get_context_data(self, **kwargs) -> dict:
        """Method to fetch the data."""
        context = super().get_context_data(**kwargs)
        context["user"] = {
            "username": self.request.user.username,
            "user_id": self.request.user.id,
        }
        context["profile"] = {
            "public_credit_name": self.request.user.profile.get_public_credit_name,
            "description": self.request.user.profile.description,
        }
        context["teams"] = [{"team": team.name, "camp": team.camp.title} for team in self.request.user.teams.all()]
        return context


class ProfilePermissionList(LoginRequiredMixin, ListView):
    """View to list all user permissions."""

    model = Permission
    template_name = "permission_list.html"
    context_object_name = "permissions"

    def get_queryset(self, *args, **kwargs) -> QuerySet:
        """Get real Permission objects so we have the perm descriptions as well."""
        query = Q()
        # loop over users permissions and build an OR query
        for perm in self.request.user.get_all_permissions():
            app_label, codename = perm.split(".")
            query |= Q(content_type__app_label=app_label, codename=codename)
        # get and return the objects
        return (
            Permission.objects.none()
            .filter(query)
            .exclude(
                codename__in=["add_camp", "change_camp", "delete_camp", "view_camp"],
            )
        )


class ProfileSessionThemeSwitchView(View):
    """View for setting the Session theme."""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """GET method for setting the Session theme."""
        theme = request.GET.get("theme") or "default"
        next_url = request.GET.get("next") or "/"
        if theme in dict(Profile.THEME_CHOICES) and next_url[:1] == "/":
            if self.request.user.is_authenticated and theme == "default":
                self.request.session["theme"] = self.request.user.profile.theme
            else:
                self.request.session["theme"] = theme
            return redirect(next_url)
        return HttpResponseForbidden()


class ProfileOIDCView(LoginRequiredMixin, FormView):
    """View for showing OIDC permissions."""

    template_name = "oidc.html"
    form_class = OIDCForm

    def setup(self, *args, **kwargs) -> None:
        """Method for initial setup of the view."""
        super().setup(*args, **kwargs)
        validator = BornhackOAuth2Validator()
        self.scopes = validator.oidc_claim_scope
        self.claims = validator.get_additional_claims(request=self.request)

    def get_form(self, form_class: type[Form] | None = None) -> Form:
        """Method for returning the form."""
        if form_class is None:
            form_class = self.get_form_class()
            self.initial["scopes"] = self.request.GET.getlist(key="scopes")
        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs) -> dict:
        """Method for collecting data used in template."""
        context = super().get_context_data(**kwargs)
        context["claims"] = {}
        for claim, value in self.claims.items():
            scope = self.scopes[claim]
            if scope in self.request.GET.getlist(key="scopes"):
                context["claims"][claim] = value
        context["scopes"] = self.scopes
        context["active_scopes"] = ["openid", *sorted(set(self.request.GET.getlist(key="scopes")))]
        context["all_scopes"] = sorted(set(self.scopes.values()))
        del context["all_scopes"][context["all_scopes"].index("openid")]
        return context


class ProfileFacilityFeedbackListView(LoginRequiredMixin, ListView):
    """View for showing all user feedback on facilities."""

    model = FacilityFeedback
    template_name = "profile_facility_feedback.html"
    context_object_name = "feedback_list"

    def get_queryset(self, *args, **kwargs) -> QuerySet:
        """Update queryset to only include own feedback."""
        return super().get_queryset().filter(user=self.request.user).order_by("handled", "created")
