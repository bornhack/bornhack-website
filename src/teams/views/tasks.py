from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import UpdateView

from ..models import TaskComment
from ..models import Team
from ..models import TeamMember
from ..models import TeamTask
from .mixins import TeamViewMixin
from .mixins import TeamTaskerPermissionMixin
from camps.mixins import CampViewMixin


class TeamTasksView(CampViewMixin, DetailView):
    template_name = "team_tasks.html"
    context_object_name = "team"
    model = Team
    slug_url_kwarg = "team_slug"
    active_menu = "tasks"


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["comment"]


class TaskDetailView(TeamViewMixin, DetailView):
    template_name = "task_detail.html"
    context_object_name = "task"
    model = TeamTask
    active_menu = "tasks"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["comment_form"] = TaskCommentForm()
        return context

    def post(self, request, **kwargs):
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
    class Meta:
        model = TeamTask
        fields = ["name", "description", "when", "completed"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["when"].widget.widgets = [
            forms.DateTimeInput(attrs={"placeholder": "Start"}),
            forms.DateTimeInput(attrs={"placeholder": "End"}),
        ]


class TaskCreateView(
    LoginRequiredMixin,
    TeamViewMixin,
    TeamTaskerPermissionMixin,
    CreateView,
):
    model = TeamTask
    template_name = "task_form.html"
    form_class = TaskForm
    active_menu = "tasks"

    def get_team(self):
        return Team.objects.get(
            camp__slug=self.kwargs["camp_slug"],
            slug=self.kwargs["team_slug"],
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


class TaskUpdateView(
    LoginRequiredMixin,
    TeamViewMixin,
    TeamTaskerPermissionMixin,
    UpdateView,
):
    model = TeamTask
    template_name = "task_form.html"
    form_class = TaskForm
    active_menu = "tasks"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.team
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
