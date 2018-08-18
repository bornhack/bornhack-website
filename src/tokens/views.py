from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

from .models import Token, TokenFind

class TokenDetailView(LoginRequiredMixin, DetailView):
    template_name = "token_detail.html"
    model = Token
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get(self, request, *args, **kwargs):
        # register this tokenview if it isn't already
        token, created = TokenFind.objects.get_or_create(
            token=self.get_object(),
            user=request.user
        )
        return super().get(request, *args, **kwargs)


class TokenFindListView(LoginRequiredMixin, ListView):
    template_name = "tokenfind_list.html"
    model = TokenFind

    def get_queryset(self):
        return TokenFind.objects.filter(user=self.request.user)

