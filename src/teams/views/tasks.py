"""All views for the teams task application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import UpdateView

from camps.mixins import CampViewMixin
from teams.models import TaskComment
from teams.models import Team
from teams.models import TeamMember
from teams.models import TeamTask
from utils.mixins import IsTeamPermContextMixin

from .mixins import TeamTaskerPermissionMixin
from .mixins import TeamViewMixin

if TYPE_CHECKING:
    from django.http import HttpRequest


class TeamTasksView(CampViewMixin, IsTeamPermContextMixin, DetailView):
    """List view of the team tasks."""

    template_name = "team_tasks.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "tasks"


class TaskCommentForm(forms.ModelForm):
    """Form for commenting on a Task."""

    class Meta:
        """Meta."""

        model = TaskComment
        fields = ("comment",)


class TaskDetailView(TeamViewMixin, IsTeamPermContextMixin, DetailView):
    """Task detail view."""

    template_name = "task_detail.html"
    context_object_name = "task"
    model = TeamTask
    active_menu = "tasks"

    def get_context_data(self, *args, **kwargs) -> dict:
        """Add the inline form for comments."""
        context = super().get_context_data(*args, **kwargs)
        context["comment_form"] = TaskCommentForm()
        return context

    def post(self, request: HttpRequest, **kwargs) -> HttpResponseRedirect:
        """Post endpoint for the comment form."""
        task = self.get_object()
        if request.user not in task.team.members.all():
            return HttpResponseNotAllowed("Nope")

        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = TeamMember.objects.get(user=request.user, team=task.team)
            comment.task = task
            comment.save()
        else:
            messages.error(request, "Something went wrong.")

        return HttpResponseRedirect(task.get_absolute_url())


class TaskForm(forms.ModelForm):
    """Form for creating or edditing Tasks."""

    class Meta:
        """Meta."""

        model = TeamTask
        fields = ("name", "description", "when", "completed")

    def __init__(self, **kwargs) -> None:
        """Method for setting up the form fields."""
        super().__init__(**kwargs)
        self.fields["when"].widget.widgets = [
            forms.DateTimeInput(attrs={"placeholder": "Start"}),
            forms.DateTimeInput(attrs={"placeholder": "End"}),
        ]


class TaskCreateView(
    LoginRequiredMixin,
    TeamViewMixin,
    TeamTaskerPermissionMixin,
    IsTeamPermContextMixin,
    CreateView,
):
    """View for creating a team task."""

    model = TeamTask
    template_name = "task_form.html"
    form_class = TaskForm
    active_menu = "tasks"

    def get_team(self) -> Team:
        """Method to get the team object."""
        return Team.objects.get(
            camp__slug=self.kwargs["camp_slug"],
            slug=self.kwargs["team_slug"],
        )

    def form_valid(self, form: TaskForm) -> HttpResponseRedirect:
        """Method to set extra fields on save."""
        task = form.save(commit=False)
        task.team = self.team
        if not task.name:
            task.name = "noname"
        task.save()
        return HttpResponseRedirect(task.get_absolute_url())

    def get_success_url(self) -> str:
        """Method to get the success url."""
        return self.get_object().get_absolute_url()


class TaskUpdateView(
    LoginRequiredMixin,
    TeamViewMixin,
    TeamTaskerPermissionMixin,
    IsTeamPermContextMixin,
    UpdateView,
):
    """Update task view used for updating tasks."""

    model = TeamTask
    template_name = "task_form.html"
    form_class = TaskForm
    active_menu = "tasks"

    def get_context_data(self, *args, **kwargs) -> dict:
        """Method for adding context data for team."""
        context = super().get_context_data(**kwargs)
        context["team"] = self.team
        return context

    def form_valid(self, form: TaskForm) -> HttpResponseRedirect:
        """Method to set extra fields on save."""
        task = form.save(commit=False)
        task.team = self.team
        if not task.name:
            task.name = "noname"
        task.save()
        return HttpResponseRedirect(task.get_absolute_url())

    def get_success_url(self) -> str:
        """Method to get the success url."""
        return self.get_object().get_absolute_url()
