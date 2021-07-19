from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from reversion.views import RevisionMixin

from camps.mixins import CampViewMixin
from info.models import InfoCategory, InfoItem

from ..models import Team
from .mixins import EnsureTeamResponsibleMixin, TeamViewMixin


class InfoCategoriesListView(
    LoginRequiredMixin,
    CampViewMixin,
    TeamViewMixin,
    EnsureTeamResponsibleMixin,
    ListView,
):
    model = InfoCategory
    template_name = "team_info_categories.html"
    slug_field = "anchor"
    active_menu = "info_categories"

    def get_team(self):
        return Team.objects.get(
            camp__slug=self.kwargs["camp_slug"], slug=self.kwargs["team_slug"]
        )


class InfoItemCreateView(
    LoginRequiredMixin,
    CampViewMixin,
    TeamViewMixin,
    EnsureTeamResponsibleMixin,
    CreateView,
):
    model = InfoItem
    template_name = "team_info_item_form.html"
    fields = ["headline", "body", "anchor", "weight"]
    slug_field = "anchor"
    active_menu = "info_categories"

    def get_team(self):
        return Team.objects.get(
            camp__slug=self.kwargs["camp_slug"], slug=self.kwargs["team_slug"]
        )

    def form_valid(self, form):
        info_item = form.save(commit=False)
        category = InfoCategory.objects.get(
            team__camp=self.camp, anchor=self.kwargs.get("category_anchor")
        )
        info_item.category = category
        info_item.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.team.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = InfoCategory.objects.get(
            team__camp__slug=self.kwargs["camp_slug"],
            anchor=self.kwargs["category_anchor"],
        )
        return context


class InfoItemUpdateView(
    LoginRequiredMixin,
    CampViewMixin,
    TeamViewMixin,
    EnsureTeamResponsibleMixin,
    RevisionMixin,
    UpdateView,
):
    model = InfoItem
    template_name = "team_info_item_form.html"
    fields = ["headline", "body", "anchor", "weight"]
    slug_field = "anchor"
    slug_url_kwarg = "item_anchor"
    active_menu = "info_categories"

    def get_team(self):
        return Team.objects.get(
            camp__slug=self.kwargs["camp_slug"], slug=self.kwargs["team_slug"]
        )

    def get_success_url(self):
        next = self.request.GET.get("next")
        if next:
            return next
        return self.team.get_absolute_url()


class InfoItemDeleteView(
    LoginRequiredMixin,
    CampViewMixin,
    TeamViewMixin,
    EnsureTeamResponsibleMixin,
    RevisionMixin,
    DeleteView,
):
    model = InfoItem
    template_name = "team_info_item_delete_confirm.html"
    slug_field = "anchor"
    slug_url_kwarg = "item_anchor"
    active_menu = "info_categories"

    def get_team(self):
        return Team.objects.get(
            camp__slug=self.kwargs["camp_slug"], slug=self.kwargs["team_slug"]
        )

    def get_success_url(self):
        next = self.request.GET.get("next")
        if next:
            return next
        return self.team.get_absolute_url()
