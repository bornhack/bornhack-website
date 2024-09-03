from django.shortcuts import get_object_or_404

from .models import Layer


class LayerViewMixin:
    """
    A mixin to get the Layer object based on layer_slug in url kwargs
    """

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.layer = get_object_or_404(Layer, slug=self.kwargs["layer_slug"])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["layer"] = self.layer
        return context
