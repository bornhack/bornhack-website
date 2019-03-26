from camps.models import Camp
from django.utils import timezone
from django.contrib import admin


def get_current_camp():
    try:
        return Camp.objects.get(camp__contains=timezone.now())
    except Camp.DoesNotExist:
        return False


class CampPropertyListFilter(admin.SimpleListFilter):
    """
    SimpleListFilter to filter models by camp when camp is
    a property and not a real model field.
    """
    title = 'Camp'
    parameter_name = 'camp'

    def lookups(self, request, model_admin):
        # get the current queryset
        qs = model_admin.get_queryset(request)

        # get a list of the unique camps in the current queryset
        unique_camps = set([item.camp for item in qs])

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
