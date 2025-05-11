"""CBV mixin to make the Camp object available, and filter querysets by camp.

Adds `self.camp` to views, and adds `camp` and `camps` to the template context.
Filters querysets with a `camp_filter` property.
"""

from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView, UpdateView, DeleteView, FormView
from django.contrib import messages
from camps.models import Camp


class CampViewMixin:
    """
    This mixin makes sure self.camp is available (taken from url kwarg camp_slug)
    It also filters out objects that belong to other camps when the model has a camp_filter
    """

    def setup(self, *args, **kwargs):
        """Set self.camp, and raise PermissionDenied if camp is readonly and it is an edit view."""
        super().setup(*args, **kwargs)
        self.camp = get_object_or_404(Camp, slug=self.kwargs["camp_slug"])
        if self.camp.read_only and isinstance(
            self,
            FormView | CreateView | UpdateView | DeleteView,
        ):
            # this camp is readonly
            messages.error(self.request, f"The camp {self.camp.title} is read-only.")
            raise PermissionDenied

    def get_queryset(self):
        """Filter querysets by camp.

        Uses the `camp_filter` property on the model. Some models can have more than one "path"
        to the Camp model, so `camp_filter` can be a string or a list of strings.
        """
        queryset = super().get_queryset()

        # do we have a camp_filter on this model
        if not hasattr(self.model, "camp_filter"):
            return queryset

        # get the camp_filter from the model
        camp_filter = self.model.get_camp_filter()

        # Let us deal with eveything as a list
        if isinstance(camp_filter, str):
            camp_filter = [camp_filter]

        for _filter in camp_filter:
            # add camp to the filter_dict
            filter_dict = {_filter: self.camp}

            # get pk from kwargs if we have it
            if hasattr(self, "pk_url_kwarg"):
                pk = self.kwargs.get(self.pk_url_kwarg)
                if pk is not None:
                    # We should also filter for the pk of the object
                    filter_dict["pk"] = pk

            # get slug from kwargs if we have it
            if hasattr(self, "slug_url_kwarg"):
                slug = self.kwargs.get(self.slug_url_kwarg)
                if slug is not None and (pk is None or self.query_pk_and_slug):
                    # we should also filter for the slug of the object
                    filter_dict[self.get_slug_field()] = slug

            # do the filtering and return the result
            result = queryset.filter(**filter_dict)
            if result.exists():
                # we got some results with this camp_filter, return now
                return result

        # no camp_filter returned any results, return an empty queryset
        return result

    def get_context_data(self, *args, **kwargs):
        """Add `camp` and `camps` to the template context."""
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "camps": Camp.objects.all().order_by("-camp"),
                "camp": self.camp,
            },
        )
        return context
