from camps.models import Camp
from django.shortcuts import get_object_or_404


class CampViewMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.camp = get_object_or_404(Camp, slug=self.kwargs['camp_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super(CampViewMixin, self).get_queryset()
        return queryset.filter(camp=self.camp)


