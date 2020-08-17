from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView

from .models import Token, TokenFind


class TokenDetailView(LoginRequiredMixin, DetailView):
    template_name = "token_detail.html"
    model = Token
    slug_field = "token"
    slug_url_kwarg = "token"
    older_code = False

    def get(self, request, *args, **kwargs):
        # register this tokenview if it isn't already
        token, created = TokenFind.objects.get_or_create(
            token=self.get_object(), user=request.user
        )
        if created:
            messages.success(
                self.request,
                f"You found a secret token: {self.get_object().description} - Your visit has been registered! Keep hunting, there might be more tokens out there.",
            )
        return redirect(reverse("tokens:tokenfind_list"))


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
