from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.views.generic import DetailView, CreateView, UpdateView
from django import forms

from camps.mixins import CampViewMixin
from ..models import Team, TeamTask
from .mixins import EnsureTeamResponsibleMixin, TeamViewMixin


class TeamTasksView(CampViewMixin, DetailView):
    template_name = "team_tasks.html"
    context_object_name = 'team'
    model = Team
    slug_url_kwarg = 'team_slug'
    active_menu = 'tasks'


class TaskDetailView(CampViewMixin, TeamViewMixin, DetailView):
    template_name = "task_detail.html"
    context_object_name = "task"
    model = TeamTask
    active_menu = 'tasks'


class TaskForm(forms.ModelForm):
    class Meta:
        model = TeamTask
        fields = ['name', 'description', 'when', 'completed']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['when'].widget.widgets = [
            forms.DateTimeInput(
                attrs={"placeholder": "Start"}
            ),
            forms.DateTimeInput(
                attrs={"placeholder": "End"}
            )
        ]


class TaskCreateView(LoginRequiredMixin, CampViewMixin, TeamViewMixin, EnsureTeamResponsibleMixin, CreateView):
    model = TeamTask
    template_name = "task_form.html"
    form_class = TaskForm
    active_menu = 'tasks'

    def get_team(self):
        return Team.objects.get(
            camp__slug=self.kwargs['camp_slug'],
            slug=self.kwargs['team_slug']
        )

    def form_valid(self, form):
        task = form.save(commit=False)
        task.team = self.team
        if not task.name:
            task.name = "noname"
        task.save()
        return HttpResponseRedirect(task.get_absolute_url())

    def get_success_url(self):
        return self.get_object().get_absolute_url()


class TaskUpdateView(LoginRequiredMixin, CampViewMixin, TeamViewMixin, EnsureTeamResponsibleMixin, UpdateView):
    model = TeamTask
    template_name = "task_form.html"
    form_class = TaskForm
    active_menu = 'tasks'

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
