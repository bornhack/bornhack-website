from camps.models import Camp
from django.shortcuts import get_object_or_404


class CampViewMixin(object):
    """
    This mixin makes sure self.camp is available (taken from url kwarg camp_slug)
    It also filters out objects that belong to other camps when the queryset has
    a direct relation to the Camp model.
    """
    def dispatch(self, request, *args, **kwargs):
        self.camp = get_object_or_404(Camp, slug=self.kwargs['camp_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super(CampViewMixin, self).get_queryset()
        if queryset:
            # check if we have a foreignkey to Camp, filter if so
            for field in queryset.model._meta.fields:
                if field.name=="camp" and field.related_model._meta.label == "camps.Camp":
                    return queryset.filter(camp=self.camp)

        # Camp relation not found, or queryset is empty, return it unaltered
        return queryset


