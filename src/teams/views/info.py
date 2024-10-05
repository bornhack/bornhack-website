from teams.views.mixins import TeamInfopagerPermissionMixin
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView
from reversion.views import RevisionMixin

from .mixins import TeamViewMixin
from info.models import InfoCategory
from info.models import InfoItem


class InfoCategoriesListView(
    TeamViewMixin,
    TeamInfopagerPermissionMixin,
    ListView,
):
    model = InfoCategory
    template_name = "team_info_categories.html"
    slug_field = "anchor"
    active_menu = "info_categories"


class InfoItemCreateView(
    TeamViewMixin,
    TeamInfopagerPermissionMixin,
    CreateView,
):
    model = InfoItem
    template_name = "team_info_item_form.html"
    fields = ["headline", "body", "anchor", "weight"]
    slug_field = "anchor"
    active_menu = "info_categories"

    def form_valid(self, form):
        info_item = form.save(commit=False)
        category = InfoCategory.objects.get(
            team__camp=self.camp,
            anchor=self.kwargs.get("category_anchor"),
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
    TeamViewMixin,
    TeamInfopagerPermissionMixin,
    RevisionMixin,
    UpdateView,
):
    model = InfoItem
    template_name = "team_info_item_form.html"
    fields = ["headline", "body", "anchor", "weight"]
    slug_field = "anchor"
    slug_url_kwarg = "item_anchor"
    active_menu = "info_categories"

    def get_success_url(self):
        next = self.request.GET.get("next")
        if next:
            return next
        return self.team.get_absolute_url()


class InfoItemDeleteView(
    TeamViewMixin,
    TeamInfopagerPermissionMixin,
    RevisionMixin,
    DeleteView,
):
    model = InfoItem
    template_name = "team_info_item_delete_confirm.html"
    slug_field = "anchor"
    slug_url_kwarg = "item_anchor"
    active_menu = "info_categories"

    def get_success_url(self):
        next = self.request.GET.get("next")
        if next:
            return next
        return self.team.get_absolute_url()
