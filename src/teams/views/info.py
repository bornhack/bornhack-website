"""View for managing the team info pages."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView
from reversion.views import RevisionMixin

from info.models import InfoCategory
from info.models import InfoItem
from teams.views.mixins import TeamInfopagerPermissionMixin
from utils.mixins import IsPermissionMixin
from utils.widgets import MarkdownWidget

from .mixins import TeamViewMixin

if TYPE_CHECKING:
    from django.forms import Form

class InfoCategoriesListView(
    TeamViewMixin,
    TeamInfopagerPermissionMixin,
    IsPermissionMixin,
    ListView,
):
    """Info Categories list view."""
    model = InfoCategory
    template_name = "team_info_categories.html"
    slug_field = "anchor"
    active_menu = "info_categories"


class InfoItemCreateView(
    TeamViewMixin,
    TeamInfopagerPermissionMixin,
    IsPermissionMixin,
    CreateView,
):
    """Info item create view."""
    model = InfoItem
    template_name = "team_info_item_form.html"
    fields = ("headline", "body", "anchor", "weight")
    slug_field = "anchor"
    active_menu = "info_categories"

    def get_form(self, *args, **kwargs) -> Form:
        """Method to update widget for body form element."""
        form = super().get_form(*args, **kwargs)
        form.fields["body"].widget = MarkdownWidget()
        return form

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        """Method for updating the category field by the category_anchor."""
        info_item = form.save(commit=False)
        category = InfoCategory.objects.get(
            team__camp=self.camp,
            anchor=self.kwargs.get("category_anchor"),
        )
        info_item.category = category
        info_item.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        """Method for creating the success/redirect url."""
        return self.team.get_absolute_url()

    def get_context_data(self, **kwargs) -> dict:
        """Method for adding category to the context."""
        context = super().get_context_data(**kwargs)
        context["category"] = InfoCategory.objects.get(
            team__camp__slug=self.kwargs["camp_slug"],
            anchor=self.kwargs["category_anchor"],
        )
        return context


class InfoItemUpdateView(
    TeamViewMixin,
    TeamInfopagerPermissionMixin,
    RevisionMixin,
    IsPermissionMixin,
    UpdateView,
):
    """Info item update view."""
    model = InfoItem
    template_name = "team_info_item_form.html"
    fields = ("headline", "body", "anchor", "weight")
    slug_field = "anchor"
    slug_url_kwarg = "item_anchor"
    active_menu = "info_categories"

    def get_form(self, *args, **kwargs) -> Form:
        """Method to update widget for body form element."""
        form = super().get_form(*args, **kwargs)
        form.fields["body"].widget = MarkdownWidget()
        return form

    def get_success_url(self) -> str:
        """Method for creating the success/redirect url."""
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return self.team.get_absolute_url()


class InfoItemDeleteView(
    TeamViewMixin,
    TeamInfopagerPermissionMixin,
    RevisionMixin,
    IsPermissionMixin,
    DeleteView,
):
    """View for deleting a info item."""
    model = InfoItem
    template_name = "team_info_item_delete_confirm.html"
    slug_field = "anchor"
    slug_url_kwarg = "item_anchor"
    active_menu = "info_categories"

    def get_success_url(self) -> str:
        """Method for creating the success/redirect url."""
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return self.team.get_absolute_url()
