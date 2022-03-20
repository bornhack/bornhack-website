from django.views.generic import DetailView
from django.views.generic import ListView

from .models import Wish


class WishListView(ListView):
    model = Wish
    template_name = "wish_list.html"

    def get_queryset(self, **kwargs):
        # only show unfulfilled wishes
        return super().get_queryset().filter(fulfilled=False)


class WishDetailView(DetailView):
    model = Wish
    template_name = "wish_detail.html"
    slug_url_kwarg = "wish_slug"
