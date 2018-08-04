from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import DetailView, CreateView, UpdateView

from camps.mixins import CampViewMixin
from ..models import TeamTask
from .mixins import EnsureTeamResponsibleMixin


class TaskDetailView(CampViewMixin, DetailView):
    template_name = "task_detail.html"
    context_object_name = "task"
    model = TeamTask


class TaskCreateView(LoginRequiredMixin, CampViewMixin, EnsureTeamResponsibleMixin, CreateView):
    model = TeamTask
    template_name = "task_form.html"
    fields = ['name', 'description', 'when', 'completed']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        return context

    def form_valid(self, form):
        task = form.save(commit=False)
        task.team = self.team
        if not task.name:
            task.name = "noname"
        task.save()
        return HttpResponseRedirect(task.get_absolute_url())

    def get_success_url(self):
        return self.get_object().get_absolute_url()


class TaskUpdateView(LoginRequiredMixin, CampViewMixin, EnsureTeamResponsibleMixin, UpdateView):
    model = TeamTask
    template_name = "task_form.html"
    fields = ['name', 'description', 'when', 'completed']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.team
        return context

    def form_valid(self, form):
        task = form.save(commit=False)
        task.team = self.team
        if not task.name:
            task.name = "noname"
        task.save()
        return HttpResponseRedirect(task.get_absolute_url())

    def get_success_url(self):
        return self.get_object().get_absolute_url()
