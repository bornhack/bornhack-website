"""View for shifts in teams application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.template import Context
from django.template import Template
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView
from django.views.generic import View
from psycopg2.extras import DateTimeTZRange

from camps.mixins import CampViewMixin
from teams.exceptions import StartAfterEndError
from teams.exceptions import StartSameAsEndError
from teams.models import Team
from teams.models import TeamMember
from teams.models import TeamShift
from teams.models import TeamShiftAssignment
from utils.mixins import IsTeamPermContextMixin

from .mixins import EnsureTeamLeadMixin

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest
    from django.http import HttpResponse
    from django.forms import ModelForm
    from camps.models import Camp


class ShiftListView(LoginRequiredMixin, CampViewMixin, IsTeamPermContextMixin, ListView):
    """Shift list view."""

    model = TeamShift
    template_name = "team_shift_list.html"
    context_object_name = "shifts"
    active_menu = "shifts"

    def get_queryset(self) -> QuerySet:
        """Method to filter by team slug."""
        queryset = super().get_queryset()
        return queryset.filter(team__slug=self.kwargs["team_slug"])

    def get_context_data(self, **kwargs) -> dict:
        """Method for setting team to context."""
        context = super().get_context_data(**kwargs)
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context


def date_choices(camp: Camp) -> list:
    """Method for making date/time choices."""
    index = 0
    minute_choices = []
    # To begin with we assume a shift can not be shorter than an hour
    shift_minimum_length = 60
    while index * shift_minimum_length < 60:  # noqa: PLR2004
        minutes = int(index * shift_minimum_length)
        minute_choices.append(minutes)
        index += 1

    def get_time_choices(date: str) -> list:
        """Method for making a list of time options."""
        time_choices = []
        for hour in range(24):
            for minute in minute_choices:
                time_label = f"{hour:02d}:{minute:02d}"
                choice_value = f"{date} {time_label}"
                time_choices.append((choice_value, choice_value))
        return time_choices

    choices = []

    current_date = camp.buildup.lower.date()
    while current_date != camp.teardown.upper.date():
        choices.append(
            (current_date, get_time_choices(current_date.strftime("%Y-%m-%d"))),
        )
        current_date += timezone.timedelta(days=1)
    return choices


class ShiftForm(forms.ModelForm):
    """Form for shifts."""

    class Meta:
        """Meta."""

        model = TeamShift
        fields = ("from_datetime", "to_datetime", "people_required")

    def __init__(self, instance: TeamShift | None = None, **kwargs) -> None:
        """Method for setting up the form."""
        camp = kwargs.pop("camp")
        super().__init__(instance=instance, **kwargs)
        self.fields["from_datetime"].widget = forms.Select(choices=date_choices(camp))
        self.fields["to_datetime"].widget = forms.Select(choices=date_choices(camp))
        if instance:
            current_tz = timezone.get_current_timezone()
            lower = instance.shift_range.lower.astimezone(current_tz).strftime(
                "%Y-%m-%d %H:%M",
            )
            upper = instance.shift_range.upper.astimezone(current_tz).strftime(
                "%Y-%m-%d %H:%M",
            )
            self.fields["from_datetime"].initial = lower
            self.fields["to_datetime"].initial = upper

    from_datetime = forms.DateTimeField()
    to_datetime = forms.DateTimeField()

    def _get_from_datetime(self) -> dict:
        """Method to convert from_datetime to current timezone."""
        current_timezone = timezone.get_current_timezone()
        return self.cleaned_data["from_datetime"].astimezone(current_timezone)

    def _get_to_datetime(self) -> dict:
        """Method to convert to_datetime to current timezone."""
        current_timezone = timezone.get_current_timezone()
        return self.cleaned_data["to_datetime"].astimezone(current_timezone)

    def clean(self) -> None:
        """Method for cleaning the form data.

        Check lower is bigger then upper
        Check lower and upper are not the same
        """
        self.lower = self._get_from_datetime()
        self.upper = self._get_to_datetime()
        if self.lower > self.upper:
            raise StartAfterEndError
        if self.lower == self.upper:
            raise StartSameAsEndError

    def save(self, commit=True) -> TeamShift:
        """Method for saving shift_range from self.lower and self.upper."""
        # self has .lower and .upper from .clean()
        self.instance.shift_range = DateTimeTZRange(self.lower, self.upper)
        return super().save(commit=commit)


class ShiftCreateView(LoginRequiredMixin, CampViewMixin, EnsureTeamLeadMixin, IsTeamPermContextMixin, CreateView):
    """View for creating a single shift."""

    model = TeamShift
    template_name = "team_shift_form.html"
    form_class = ShiftForm
    active_menu = "shifts"

    def get_form_kwargs(self) -> dict:
        """Method for adding camp to kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs["camp"] = self.camp
        return kwargs

    def form_valid(self, form: ShiftForm) -> HttpResponse:
        """Check if the form is valid add team to the data."""
        shift = form.save(commit=False)
        shift.team = Team.objects.get(camp=self.camp, slug=self.kwargs["team_slug"])
        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> dict:
        """Method for adding camp and team slug to context."""
        context = super().get_context_data(**kwargs)
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context

    def get_success_url(self) -> str:
        """Method get success url."""
        return reverse("teams:shifts", kwargs=self.kwargs)


class ShiftUpdateView(LoginRequiredMixin, CampViewMixin, EnsureTeamLeadMixin, IsTeamPermContextMixin, UpdateView):
    """View for updating a single shift."""

    model = TeamShift
    template_name = "team_shift_form.html"
    form_class = ShiftForm
    active_menu = "shifts"

    def get_form_kwargs(self) -> dict:
        """Method for adding camp to kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs["camp"] = self.camp
        return kwargs

    def get_context_data(self, **kwargs) -> dict:
        """Method for adding team to context."""
        context = super().get_context_data(**kwargs)
        context["team"] = self.object.team
        return context

    def get_success_url(self) -> str:
        """Method get success url."""
        self.kwargs.pop("pk")
        return reverse("teams:shifts", kwargs=self.kwargs)


class ShiftDeleteView(LoginRequiredMixin, CampViewMixin, EnsureTeamLeadMixin, IsTeamPermContextMixin, DeleteView):
    """View for deleting a shift."""

    model = TeamShift
    template_name = "team_shift_confirm_delete.html"
    active_menu = "shifts"

    def get_context_data(self, **kwargs) -> dict:
        """Method for adding camp and team slug to context."""
        context = super().get_context_data(**kwargs)
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context

    def get_success_url(self) -> str:
        """Method get success url."""
        self.kwargs.pop("pk")
        return reverse("teams:shifts", kwargs=self.kwargs)


class MultipleShiftForm(forms.Form):
    """Form for creating multple shifts."""

    def __init__(self, instance: dict | None = None, **kwargs) -> None:
        """Method for form init setting camp to kwargs."""
        camp = kwargs.pop("camp")
        super().__init__(**kwargs)
        self.fields["from_datetime"].widget = forms.Select(choices=date_choices(camp))

    from_datetime = forms.DateTimeField()

    number_of_shifts = forms.IntegerField(help_text="How many shifts?")

    shift_length = forms.IntegerField(
        help_text="How long should a shift be in minutes?",
    )

    people_required = forms.IntegerField()


class ShiftCreateMultipleView(LoginRequiredMixin, CampViewMixin, EnsureTeamLeadMixin, IsTeamPermContextMixin, FormView):
    """View for creating multiple shifts."""

    template_name = "team_shift_form.html"
    form_class = MultipleShiftForm
    active_menu = "shifts"

    def get_form_kwargs(self) -> dict:
        """Method for setting camp to the kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs["camp"] = self.camp
        return kwargs

    def form_valid(self, form: MultipleShiftForm) -> HttpResponse:
        """Method for checking if the form data is valid."""
        team = Team.objects.get(camp=self.camp, slug=self.kwargs["team_slug"])
        current_timezone = timezone.get_current_timezone()

        start_datetime = form.cleaned_data["from_datetime"].astimezone(current_timezone)
        number_of_shifts = form.cleaned_data["number_of_shifts"]
        shift_length = form.cleaned_data["shift_length"]
        people_required = form.cleaned_data["people_required"]

        shifts = []
        for _index in range(number_of_shifts):
            shift_range = DateTimeTZRange(
                start_datetime,
                start_datetime + timezone.timedelta(minutes=shift_length),
            )
            shifts.append(
                TeamShift(
                    team=team,
                    people_required=people_required,
                    shift_range=shift_range,
                ),
            )
            start_datetime += timezone.timedelta(minutes=shift_length)

        TeamShift.objects.bulk_create(shifts)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Method for returning the success url."""
        return reverse("teams:shifts", kwargs=self.kwargs)

    def get_context_data(self, **kwargs) -> dict:
        """Method for adding team to the context."""
        context = super().get_context_data(**kwargs)
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context


class MemberTakesShift(LoginRequiredMixin, CampViewMixin, UpdateView):
    """View for adding a user to a shift."""
    model = TeamShift
    fields = []
    template_name = "team_shift_confirm_action.html"
    context_object_name = "shifts"
    active_menu = "shifts"

    def get_context_data(self, **kwargs) -> dict[str, object]:
        """Method for setting the page context data."""
        context = super().get_context_data(**kwargs)
        context['action'] = f"Are you sure you want to take this {self.object}?"
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context

    def form_valid(self, form: ModelForm[TeamShift]) -> HttpResponseRedirect:
        """Method for adding user to a shift."""
        shift = self.object 
        team = self.object.team 

        team_member = TeamMember.objects.get(team=team, user=self.request.user)

        overlapping_shifts = TeamShift.objects.filter(
            team__camp=self.camp,
            team_members__user=self.request.user,
            shift_range__overlap=shift.shift_range,
        )

        if overlapping_shifts.exists():
            template = Template(
                """You have shifts overlapping with the one you are trying to assign:<br/> <ul>
            {% for shift in shifts %}
            <li>{{ shift }}</li>
            {% endfor %}
            </ul>
            """,
            )
            messages.error(
                self.request,
                template.render(Context({"shifts": overlapping_shifts})),
            )
        else:
            # Remove at most one shift assignment for sale if any
            # When a shift is for sale and a user presses assign its first assigning the for sale one
            for shift_assignment in shift.team_members.filter(teamshiftassignment__for_sale=True)[:1]:
                shift.team_members.remove(shift_assignment)
            shift.team_members.add(team_member)

        self.kwargs.pop("pk")

        return HttpResponseRedirect(reverse("teams:shifts", kwargs=self.kwargs))


class MemberDropsShift(LoginRequiredMixin, CampViewMixin, UpdateView):
    model = TeamShift
    fields = []
    template_name = "team_shift_confirm_action.html"
    context_object_name = "shifts"
    active_menu = "shifts"
    """View for remove a user from a shift."""

    def get_context_data(self, **kwargs) -> dict[str, object]:
        """Method for setting the page context data."""
        context = super().get_context_data(**kwargs)
        context['action'] = f"Are you sure you want to drop this {self.object}?"
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context

    def form_valid(self, form: ModelForm[TeamShift]) -> HttpResponseRedirect:
        """Method to remove user from shift."""
        shift = self.object 
        team = Team.objects.get(camp=self.camp, slug=self.kwargs["team_slug"])

        team_member = TeamMember.objects.get(team=team, user=self.request.user)

        shift.team_members.remove(team_member)

        self.kwargs.pop("pk")

        return HttpResponseRedirect(reverse("teams:shifts", kwargs=self.kwargs))


class MemberSellsShift(LoginRequiredMixin, CampViewMixin, UpdateView):
    """View for making a shift available for other user to take."""
    model = TeamShift
    fields = []
    template_name = "team_shift_confirm_action.html"
    context_object_name = "shifts"
    active_menu = "shifts"

    def get_context_data(self, **kwargs) -> dict[str, object]:
        """Method for setting the page context data."""
        context = super().get_context_data(**kwargs)
        context['action'] = f"Are you sure you want to this {self.object} available to others?"
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context

    http_methods = ("get",)

    def form_valid(self, form: ModelForm[TeamShift]) -> HttpResponseRedirect:
        """Method for making a shift available for other user to take."""
        shift = self.object
        team = Team.objects.get(camp=self.camp, slug=self.kwargs["team_slug"])

        team_member = TeamMember.objects.get(team=team, user=self.request.user)

        shift_assignment = TeamShiftAssignment.objects.get(team_member=team_member, team_shift=shift)
        shift_assignment.for_sale = True
        shift_assignment.save()

        self.kwargs.pop("pk")

        return HttpResponseRedirect(reverse("teams:shifts", kwargs=self.kwargs))


class UserShifts(CampViewMixin, TemplateView):
    """View for showing shifts for current user."""

    template_name = "team_user_shifts.html"

    def get_context_data(self, **kwargs) -> dict:
        """Method for adding user_teams and user_shits to context."""
        context = super().get_context_data(**kwargs)
        context["user_teams"] = self.request.user.teammember_set.filter(
            team__camp=self.camp,
        )
        context["user_shifts"] = TeamShift.objects.filter(
            team__camp=self.camp,
            team_members__user=self.request.user,
        )
        return context
