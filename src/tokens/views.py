from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.views.generic import ListView, DetailView

from utils.models import CampReadOnlyModeError
from .models import Token, TokenFind


class TokenDetailView(LoginRequiredMixin, DetailView):
    template_name = "token_detail.html"
    model = Token
    slug_field = "token"
    slug_url_kwarg = "token"
    older_code = False

    def get(self, request, *args, **kwargs):
        # register this tokenview if it isn't already
        try:
            token, created = TokenFind.objects.get_or_create(
                token=self.get_object(), user=request.user
            )
            return super().get(request, *args, **kwargs)
        except CampReadOnlyModeError:
            self.older_code = True
            self.older_token_token = settings.BORNHACK_2019_OLD_TOKEN_TOKEN
            return super().get(request, *args, **kwargs)


class TokenFindListView(LoginRequiredMixin, ListView):
    model = Token
    template_name = "tokens/tokenfind_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # find the tokens the user still needs to find
        tokenfinds = TokenFind.objects.filter(user=self.request.user).values_list(
            "token__id", flat=True
        )
        context["unfound_list"] = Token.objects.all().exclude(id__in=tokenfinds)
        return context
