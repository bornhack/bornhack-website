from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, UpdateView
from reversion.views import RevisionMixin

from camps.mixins import CampViewMixin
from info.models import InfoItem, InfoCategory
from teams.views.mixins import EnsureTeamResponsibleMixin


class InfoItemCreateView(LoginRequiredMixin, CampViewMixin, EnsureTeamResponsibleMixin, CreateView):
    model = InfoItem
    template_name = "info_item_form.html"
    fields = ['headline', 'body', 'anchor', 'weight']
    slug_field = 'anchor'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        return context

    def form_valid(self, form):
        info_item = form.save(commit=False)
        category = InfoCategory.objects.get(camp=self.camp, anchor=self.kwargs.get('category_anchor'))
        info_item.category = category
        info_item.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.team.get_absolute_url()


class InfoItemUpdateView(LoginRequiredMixin, CampViewMixin, EnsureTeamResponsibleMixin, RevisionMixin, UpdateView):
    model = InfoItem
    template_name = "info_item_form.html"
    fields = ['headline', 'body', 'anchor', 'weight']
    slug_field = 'anchor'
    slug_url_kwarg = 'anchor'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        return context

    def get_success_url(self):
        return self.team.get_absolute_url()

