from camps.models import Camp
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property


class CampViewMixin(object):
    """
    This mixin makes sure self.camp is available (taken from url kwarg camp_slug)
    It also filters out objects that belong to other camps when the queryset has
    a direct relation to the Camp model.
    """

    def dispatch(self, request, *args, **kwargs):
        self.camp = get_object_or_404(Camp, slug=self.kwargs["camp_slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super(CampViewMixin, self).get_queryset()
        if queryset:
            camp_filter = self.model.get_camp_filter()

            # Let us deal with eveything as a list
            if isinstance(camp_filter, str):
                camp_filter = [camp_filter]

            for _filter in camp_filter:
                result = queryset.filter(**{_filter: self.camp})
                if result.exists():
                    return result

        # Camp relation not found, or queryset is empty, return it unaltered
        return queryset
