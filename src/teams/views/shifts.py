from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, ListView, FormView
from django import forms
from django.contrib.postgres.forms.ranges import RangeWidget
from django.utils import timezone
from django.urls import reverse

from psycopg2.extras import DateTimeTZRange

from camps.mixins import CampViewMixin

from ..models import (
    Team,
    TeamShift,
)


class ShiftListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = TeamShift
    template_name = "shifts/shift_list.html"
    context_object_name = "shifts"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(team__slug=self.kwargs['team_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs['team_slug']
        )
        return context


def time_choices():
    index = 0
    minute_choices = []
    SHIFT_MINIMUM_LENGTH = 15  # TODO: Maybe this should be configurable per team?
    while index * SHIFT_MINIMUM_LENGTH < 60:
        minutes = int(index * SHIFT_MINIMUM_LENGTH)
        minute_choices.append(minutes)
        index += 1

    time_choices = []
    for hour in range(0, 24):
        for minute in minute_choices:
            choice_label = "{hour:02d}:{minutes:02d}".format(hour=hour, minutes=minute)
            time_choices.append((choice_label, choice_label))

    return time_choices


class ShiftForm(forms.ModelForm):
    class Meta:
        model = TeamShift
        fields = [
            'from_date',
            'from_time',
            'to_date',
            'to_time',
            'people_required'
        ]

    def __init__(self, instance=None, **kwargs):
        super().__init__(instance=instance, **kwargs)
        if instance:
            current_tz = timezone.get_current_timezone()

            lower = instance.shift_range.lower.astimezone(current_tz)
            upper = instance.shift_range.upper.astimezone(current_tz)

            from_date = lower.strftime('%Y-%m-%d')
            from_time = lower.strftime('%H:%M')
            to_date = upper.strftime('%Y-%m-%d')
            to_time = upper.strftime('%H:%M')

            self.fields['from_date'].initial = from_date
            self.fields['from_time'].initial = from_time
            self.fields['to_date'].initial = to_date
            self.fields['to_time'].initial = to_time

    from_date = forms.DateField(
        help_text="Format is YYYY-MM-DD"
    )

    from_time = forms.ChoiceField(
        choices=time_choices
    )

    to_date = forms.DateField(
        help_text="Format is YYYY-MM-DD"
    )

    to_time = forms.ChoiceField(
        choices=time_choices
    )

    def save(self, commit=True):
        from_string = "{} {}".format(
            self.cleaned_data['from_date'],
            self.cleaned_data['from_time']
        )
        to_string = "{} {}".format(
            self.cleaned_data['to_date'],
            self.cleaned_data['to_time']
        )
        datetime_format = '%Y-%m-%d %H:%M'
        current_timezone = timezone.get_current_timezone()
        lower = (
            timezone.datetime
            .strptime(from_string, datetime_format)
            .astimezone(current_timezone)
        )
        upper = (
            timezone.datetime
            .strptime(to_string, datetime_format)
            .astimezone(current_timezone)
        )
        self.instance.shift_range = DateTimeTZRange(lower, upper)
        return super().save(commit=commit)



class ShiftCreateView(LoginRequiredMixin, CampViewMixin, CreateView):
    model = TeamShift
    template_name = "shifts/shift_form.html"
    form_class = ShiftForm

    def form_valid(self, form):
        shift = form.save(commit=False)
        shift.team = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs['team_slug']
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'teams:shift_list',
            kwargs=self.kwargs
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs['team_slug']
        )
        return context


class ShiftUpdateView(LoginRequiredMixin, CampViewMixin, UpdateView):
    model = TeamShift
    template_name = "shifts/shift_form.html"
    form_class = ShiftForm

    def get_success_url(self):
        self.kwargs.pop('pk')
        return reverse(
            'teams:shift_list',
            kwargs=self.kwargs
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = self.object.team
        return context


class MultipleShiftForm(forms.Form):

    date = forms.DateField(
        help_text="Format is YYYY-MM-DD"
    )

    number_of_shifts = forms.IntegerField(
        help_text="How many shifts in a day?"
    )

    start_time = forms.TimeField(
        help_text="When the first shift should start? Defaults to 00:00.",
        required=False,
        initial="00:00"
    )

    end_time = forms.TimeField(
        help_text="When the last shift should end? Defaults to 00:00 (next day).",
        required=False,
        initial="00:00"
    )

    people_required = forms.IntegerField()


class ShiftCreateMultipleView(LoginRequiredMixin, CampViewMixin, FormView):
    template_name = "shifts/shift_form.html"
    form_class = MultipleShiftForm

    def form_valid(self, form):
        team = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs['team_slug']
        )
        date = form.cleaned_data['date']
        number_of_shifts = form.cleaned_data['number_of_shifts']
        start_time = form.cleaned_data['start_time']
        end_time = form.cleaned_data['end_time']
        people_required = form.cleaned_data['people_required']

        current_timezone = timezone.get_current_timezone()

        # create start datetime
        start_datetime = (
            timezone.datetime.combine(date, start_time)
            .astimezone(current_timezone)
        )
        # create end datetime
        if end_time == "00:00":
            # if end time is midnight, we want midnight for next day
            date = date + timezone.timedelta(days=1)

        end_datetime = (
            timezone.datetime.combine(date, end_time)
            .astimezone(current_timezone)
        )
        # figure out minutes between start and end datetime
        total_minutes = (end_datetime - start_datetime).total_seconds() / 60
        # divide by number of shifts -> duration for each shift
        shift_duration = total_minutes / number_of_shifts

        shifts = []
        for index in range(number_of_shifts + 1):
            shift_range = DateTimeTZRange(
                start_datetime,
                start_datetime + timezone.timedelta(minutes=shift_duration),
            )
            shifts.append(TeamShift(
                team=team,
                people_required=people_required,
                shift_range=shift_range
            ))
            start_datetime += timezone.timedelta(minutes=shift_duration)

        TeamShift.objects.bulk_create(shifts)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'teams:shift_list',
            kwargs=self.kwargs
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['team'] = Team.objects.get(
            camp=self.camp,
            slug=self.kwargs['team_slug']
        )
        return context
