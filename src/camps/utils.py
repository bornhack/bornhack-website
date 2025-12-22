from __future__ import annotations

from django.contrib import admin
from django.utils import timezone

from camps.models import Camp
from economy.models import Pos


def get_current_camp():
    try:
        return Camp.objects.get(camp__contains=timezone.now())
    except Camp.DoesNotExist:
        return False


class CampPropertyListFilter(admin.SimpleListFilter):
    """SimpleListFilter to filter models by camp when camp is
    a property and not a real model field.
    """

    title = "Camp"
    parameter_name = "camp"

    def lookups(self, request, model_admin):
        # get the current queryset
        qs = model_admin.get_queryset(request)

        # get a list of the unique camps in the current queryset
        unique_camps = {item.camp for item in qs}

        # loop over camps and yield each as a tuple
        for camp in unique_camps:
            yield (camp.slug, camp.title)

    def queryset(self, request, queryset):
        # if self.value() is None return everything
        if not self.value():
            return queryset

        # ok, get the Camp
        try:
            camp = Camp.objects.get(slug=self.value())
        except Camp.DoesNotExist:
            # camp not found, return nothing
            return queryset.model.objects.none()

        # filter out items related to other camps
        for item in queryset:
            if item.camp != camp:
                queryset = queryset.exclude(pk=item.pk)
        return queryset


def get_closest_camp(timestamp, max_days_from_prev: int=0):
    """Return the Camp object happening closest to the provided datetime."""
    # is the timestamp during a camp?
    try:
        return Camp.objects.get(
            buildup__startswith__lt=timestamp,
            teardown__endswith__gt=timestamp,
        )
    except Camp.DoesNotExist:
        pass

    # get the upcoming/next camp after the timestamp
    try:
        next_camp = Camp.objects.filter(buildup__startswith__gt=timestamp).last()
    except Pos.DoesNotExist:
        next_camp = None

    # get the previous camp before the timestamp
    try:
        prev_camp = Camp.objects.filter(teardown__endswith__lt=timestamp).first()
    except Pos.DoesNotExist:
        prev_camp = None

    if not prev_camp:
        # no bornhack happened before the timestamp
        return next_camp

    if not next_camp:
        # no bornhack happened after the timestamp
        return prev_camp

    # calculate timedeltas
    time_since_prev = timestamp - prev_camp.teardown.upper
    time_until_next = next_camp.buildup.lower - timestamp

    if time_since_prev > time_until_next or ( max_days_from_prev and time_since_prev.days > max_days_from_prev):
        # timestamp is closer to the next camp or max_days_from_prev was exceeded
        return next_camp
    # timestamp is closer to the previous camp
    return prev_camp
