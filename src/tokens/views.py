from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from prometheus_client import Gauge

from .models import Token
from .models import TokenFind
from utils.models import CampReadOnlyModeError

TOKEN_FINDS = Gauge('bornhack_tokengame_token_finds_total', 'The total number of token finds by camp, user and token', ["camp", "user_id", "username", "token_id"])
FIRST_TOKEN_FINDS = Gauge('bornhack_tokengame_first_token_finds_total', 'The tokens found for the first time', ["camp", "user_id", "username", "token_id"])

class TokenFindView(LoginRequiredMixin, DetailView):
    model = Token
    slug_field = "token"
    slug_url_kwarg = "token"

    def get(self, request, *args, **kwargs):
        # register this token find if it isn't already
        try:
            token, created = TokenFind.objects.get_or_create(
                token=self.get_object(),
                user=request.user,
            )
        except CampReadOnlyModeError:
            raise Http404

        if created:
            # user found a new token
            username = request.user.profile.get_public_credit_name
            if username == "Unnamed":
                username == "anonymous_player_{request.user.id}"

            # register metrics
            if TokenFind.objects.filter(token=self.get_object()).count() == 1:
                # this is the first time this token has been found, count it as such
                FIRST_TOKEN_FINDS.labels(token.camp.title, request.user.id, username, token.id).inc()
            TOKEN_FINDS.labels(token.camp.title, request.user.id, username, token.id).inc()

            # message for the user
            messages.success(
                self.request,
                f"Congratulations! You found a secret token: {self.get_object().description} - Your visit has been registered! Keep hunting, there might be more tokens out there.",
            )
        return redirect(reverse("tokens:tokenfind_list"))


class TokenFindListView(LoginRequiredMixin, ListView):
    model = Token
    template_name = "tokenfind_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # find the tokens the user still needs to find
        tokenfinds = TokenFind.objects.filter(user=self.request.user).values_list(
            "token__id",
            flat=True,
        )
        context["unfound_list"] = Token.objects.all().exclude(id__in=tokenfinds)
        return context
