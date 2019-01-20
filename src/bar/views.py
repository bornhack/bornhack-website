from camps.mixins import CampViewMixin
from .models import ProductCategory
from django.views.generic import ListView


class MenuView(CampViewMixin, ListView):
    model = ProductCategory
    template_name = "bar_menu.html"
    context_object_name = "categories"

    def get_queryset(self):
        return super().get_queryset().filter(camp=self.camp)
