from django.views.generic import DetailView, ListView

from .models import Wish


class WishListView(ListView):
    model = Wish
    template_name = "wish_list.html"


class WishDetailView(DetailView):
    model = Wish
    template_name = "wish_detail.html"
    slug_url_kwarg = "wish_slug"
