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

from ..models import Team
from ..models import TeamMember
from ..models import TeamShift
from camps.mixins import CampViewMixin


class ShiftListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = TeamShift
    template_name = "team_shift_list.html"
    context_object_name = "shifts"
    active_menu = "shifts"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(team__slug=self.kwargs["team_slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context


def date_choices(camp):
    index = 0
    minute_choices = []
    # To begin with we assume a shift can not be shorter than an hour
    SHIFT_MINIMUM_LENGTH = 60
    while index * SHIFT_MINIMUM_LENGTH < 60:
        minutes = int(index * SHIFT_MINIMUM_LENGTH)
        minute_choices.append(minutes)
        index += 1

    def get_time_choices(date):
        time_choices = []
        for hour in range(0, 24):
            for minute in minute_choices:
                time_label = "{hour:02d}:{minutes:02d}".format(
                    hour=hour,
                    minutes=minute,
                )
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
    class Meta:
        model = TeamShift
        fields = ["from_datetime", "to_datetime", "people_required"]

    def __init__(self, instance=None, **kwargs):
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

    def _get_from_datetime(self):
        current_timezone = timezone.get_current_timezone()
        return self.cleaned_data["from_datetime"].astimezone(current_timezone)

    def _get_to_datetime(self):
        current_timezone = timezone.get_current_timezone()
        return self.cleaned_data["to_datetime"].astimezone(current_timezone)

    def clean(self):
        self.lower = self._get_from_datetime()
        self.upper = self._get_to_datetime()
        if self.lower > self.upper:
            raise forms.ValidationError("Start can not be after end.")

    def save(self, commit=True):
        # self has .lower and .upper from .clean()
        self.instance.shift_range = DateTimeTZRange(self.lower, self.upper)
        return super().save(commit=commit)


class ShiftCreateView(LoginRequiredMixin, CampViewMixin, CreateView):
    model = TeamShift
    template_name = "team_shift_form.html"
    form_class = ShiftForm
    active_menu = "shifts"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["camp"] = self.camp
        return kwargs

    def form_valid(self, form):
        shift = form.save(commit=False)
        shift.team = Team.objects.get(camp=self.camp, slug=self.kwargs["team_slug"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("teams:shifts", kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context


class ShiftUpdateView(LoginRequiredMixin, CampViewMixin, UpdateView):
    model = TeamShift
    template_name = "team_shift_form.html"
    form_class = ShiftForm
    active_menu = "shifts"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["camp"] = self.camp
        return kwargs

    def get_success_url(self):
        self.kwargs.pop("pk")
        return reverse("teams:shifts", kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.object.team
        return context


class ShiftDeleteView(LoginRequiredMixin, CampViewMixin, DeleteView):
    model = TeamShift
    template_name = "team_shift_confirm_delete.html"
    active_menu = "shifts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context

    def get_success_url(self):
        self.kwargs.pop("pk")
        return reverse("teams:shifts", kwargs=self.kwargs)


class MultipleShiftForm(forms.Form):
    def __init__(self, instance=None, **kwargs):
        camp = kwargs.pop("camp")
        super().__init__(**kwargs)
        self.fields["from_datetime"].widget = forms.Select(choices=date_choices(camp))

    from_datetime = forms.DateTimeField()

    number_of_shifts = forms.IntegerField(help_text="How many shifts?")

    shift_length = forms.IntegerField(
        help_text="How long should a shift be in minutes?",
    )

    people_required = forms.IntegerField()


class ShiftCreateMultipleView(LoginRequiredMixin, CampViewMixin, FormView):
    template_name = "team_shift_form.html"
    form_class = MultipleShiftForm
    active_menu = "shifts"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["camp"] = self.camp
        return kwargs

    def form_valid(self, form):
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

    def get_success_url(self):
        return reverse("teams:shifts", kwargs=self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs["team_slug"],
        )
        return context


class MemberTakesShift(LoginRequiredMixin, CampViewMixin, View):
    http_methods = ["get"]

    def get(self, request, **kwargs):
        shift = TeamShift.objects.get(id=kwargs["pk"])
        team = Team.objects.get(camp=self.camp, slug=kwargs["team_slug"])

        team_member = TeamMember.objects.get(team=team, user=request.user)

        overlapping_shifts = TeamShift.objects.filter(
            team__camp=self.camp,
            team_members__user=request.user,
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
                request,
                template.render(Context({"shifts": overlapping_shifts})),
            )
        else:
            shift.team_members.add(team_member)

        kwargs.pop("pk")

        return HttpResponseRedirect(reverse("teams:shifts", kwargs=kwargs))


class MemberDropsShift(LoginRequiredMixin, CampViewMixin, View):
    http_methods = ["get"]

    def get(self, request, **kwargs):
        shift = TeamShift.objects.get(id=kwargs["pk"])
        team = Team.objects.get(camp=self.camp, slug=kwargs["team_slug"])

        team_member = TeamMember.objects.get(team=team, user=request.user)

        shift.team_members.remove(team_member)

        kwargs.pop("pk")

        return HttpResponseRedirect(reverse("teams:shifts", kwargs=kwargs))


class UserShifts(CampViewMixin, TemplateView):
    template_name = "team_user_shifts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_teams"] = self.request.user.teammember_set.filter(
            team__camp=self.camp,
        )
        context["user_shifts"] = TeamShift.objects.filter(
            team__camp=self.camp,
            team_members__user=self.request.user,
        )
        return context
