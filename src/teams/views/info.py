from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, UpdateView, DeleteView
from reversion.views import RevisionMixin

from camps.mixins import CampViewMixin
from info.models import InfoItem, InfoCategory
from .mixins import EnsureTeamResponsibleMixin, TeamViewMixin


class InfoItemCreateView(LoginRequiredMixin, CampViewMixin, TeamViewMixin, EnsureTeamResponsibleMixin, CreateView):
    model = InfoItem
    template_name = "info_item_form.html"
    fields = ['headline', 'body', 'anchor', 'weight']
    slug_field = 'anchor'

    def form_valid(self, form):
        info_item = form.save(commit=False)
        category = InfoCategory.objects.get(camp=self.camp, anchor=self.kwargs.get('category_anchor'))
        info_item.category = category
        info_item.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.team.get_absolute_url()


class InfoItemUpdateView(LoginRequiredMixin, CampViewMixin, TeamViewMixin, EnsureTeamResponsibleMixin, RevisionMixin, UpdateView):
    model = InfoItem
    template_name = "info_item_form.html"
    fields = ['headline', 'body', 'anchor', 'weight']
    slug_field = 'anchor'
    slug_url_kwarg = 'item_anchor'

    def get_success_url(self):
        next = self.request.GET.get('next')
        if next:
            return next
        return self.team.get_absolute_url()


class InfoItemDeleteView(LoginRequiredMixin, CampViewMixin, TeamViewMixin, EnsureTeamResponsibleMixin, RevisionMixin, DeleteView):
    model = InfoItem
    template_name = "info_item_delete_confirm.html"
    slug_field = 'anchor'
    slug_url_kwarg = 'item_anchor'

    def get_success_url(self):
        next = self.request.GET.get('next')
        if next:
            return next
        return self.team.get_absolute_url()
