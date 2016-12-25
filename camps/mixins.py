from django.views.generic.detail import SingleObjectMixin
from camps.models import Camp
from django.shortcuts import get_object_or_404


class CampViewMixin(Object):
    def dispatch(self, request, *args, **kwargs):
        self.camp = get_object_or_404(Camp, slug=self.kwargs.camp_slug)
        return super(CampViewMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.objects.filter(camp=self.camp)

