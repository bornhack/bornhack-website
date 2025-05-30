"""All views for the Token application."""

from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Min
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import FormView
from prometheus_client import Gauge

if TYPE_CHECKING:
    from django.db.models import QuerySet

from camps.models import Camp
from tokens.forms import TokenFindSubmitForm
from utils.models import CampReadOnlyModeError

from .models import Token
from .models import TokenFind

logger = logging.getLogger(f"bornhack.{__name__}")


TOKEN_FINDS = Gauge(
    "bornhack_tokengame_token_finds_total",
    "The total number of token finds by camp, user and token",
    ["camp", "user_id", "username", "token_id"],
)
FIRST_TOKEN_FINDS = Gauge(
    "bornhack_tokengame_first_token_finds_total",
    "The tokens found for the first time",
    ["camp", "user_id", "username", "token_id"],
)


class TokenDashboardListView(LoginRequiredMixin, ListView):
    """A View with a list of active tokens one can find."""

    model = Token
    template_name = "token_dashboard.html"

    def get_queryset(self) -> QuerySet:
        """Get active tokens filtered by camp slug"""
        qs = super().get_queryset()
        return qs.filter(active=True).filter(camp=self.request.camp)

    def get_context_data(self, **kwargs):
        """Get all of the metrics for statistics not included by the queryset"""
        context = super().get_context_data(**kwargs)

        context["form"] = TokenFindSubmitForm()

        user_tokens = TokenFind.objects.filter(
            user=self.request.user).filter(token__camp=self.request.camp.pk)
        context["user_tokens"] = user_tokens

        all_tokens = context["object_list"]
        context["user_missing_tokens"] = len(all_tokens) - len(user_tokens)

        context["total_players_stats"] = {
            "count": self.total_player_count(),
            "last_join": self.time_since_last_new_join()
        }

        found_pct, not_found_pct = self.token_found_percentages()
        context["token_finds_stats"] = {
            "count": TokenFind.objects.filter(
                token__camp=self.request.camp.pk).filter(token__active=True).count(),
            "last_found": self.last_token_found(),
            "found_pct": f"{found_pct:.1f}",
            "not_found_pct": f"{not_found_pct:.1f}"
        }

        return context

    def total_player_count(self) -> int:
        """Find count of players submitting tokens for this camp"""
        return TokenFind.objects.filter(
            token__camp=self.request.camp.pk
        ).distinct("user").count()

    def time_since_last_new_join(self) -> int:
        """
        Return the time since the last new player joined the game
        by submitting a token
        """
        last_new_join = User.objects.filter(
            token_finds__isnull = False,
            token_finds__token__camp = self.request.camp.pk
        ).annotate(latest_token_find=Min("token_finds__created")).order_by("-latest_token_find").first().latest_token_find
        delta = timezone.now() - last_new_join
        return int(delta.total_seconds() // 60)

    def last_token_found(self) -> int:
        """
        Retrieve the last token found and return the time delta in minutes
        """
        last_found = TokenFind.objects.filter(
            token__camp=self.request.camp.pk
        ).order_by("-created").first()
        delta = timezone.now() - last_found.created
        return int(delta.total_seconds() // 60)

    def token_found_percentages(self) -> tuple[int, int]:
        """Return percentage for tokens found and not found"""
        active_tokens = Token.objects.filter(camp=self.request.camp.pk).filter(active=True).count()
        tokens_found = TokenFind.objects.filter(
            token__camp=self.request.camp.pk).distinct("token").count()
        pct = (tokens_found / active_tokens) * 100
        return pct, (100 - pct)


class TokenSubmitFormView(LoginRequiredMixin, FormView):
    """View for submitting a token form"""

    form_class = TokenFindSubmitForm
    template_name = "token_submit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_data = {"token": self.kwargs.get("token")}
        context["form"] = TokenFindSubmitForm(initial=form_data)
        return context

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        """Return success url when form is valid"""
        cleaned_token = form.cleaned_data.get("token")
        try:
            token = Token.objects.get(token=cleaned_token)
        except Token.DoesNotExist:
            messages.error(
                self.request,
                "We did not recognize the token you submitted. Please try something else.",
            )
            return redirect(reverse("tokens:dashboard", kwargs={"camp_slug": self.request.camp.slug}))

        if not token.active:
            messages.warning(
                self.request,
                "Patience! You found a valid token, but it is not active. Try again later!",
            )
            return redirect(reverse("tokens:dashboard", kwargs={"camp_slug": self.request.camp.slug}))

        if token.valid_when:
            if token.valid_when.lower and token.valid_when.lower > timezone.now():
                messages.warning(
                    self.request,
                    f"This token is not valid yet! Try again after {token.valid_when.lower}",
                )
                return redirect(reverse("tokens:dashboard", kwargs={"camp_slug": self.request.camp.slug}))

            if token.valid_when.upper and token.valid_when.upper < timezone.now():
                messages.warning(
                    self.request,
                    f"This token is not valid after {token.valid_when.upper}! Maybe find a flux capacitor?",
                )
                return redirect(reverse("tokens:dashboard", kwargs={"camp_slug": self.request.camp.slug}))

        try:
            token_find, created = TokenFind.objects.get_or_create(
                token=token,
                user=self.request.user,
            )
        except CampReadOnlyModeError as e:
            raise Http404 from e

        if created:
            # user found a new token
            username = self.request.user.profile.get_public_credit_name
            if username == "Unnamed":
                username = "anonymous_player_{request.user.id}"

            # register metrics
            if TokenFind.objects.filter(token=token).count() == 1:
                # this is the first time this token has been found, count it as such
                FIRST_TOKEN_FINDS.labels(
                    token.camp.title,
                    self.request.user.id,
                    username,
                    token.id,
                ).inc()
            TOKEN_FINDS.labels(
                token.camp.title,
                self.request.user.id,
                username,
                token.id,
            ).inc()

            # message for the user
            messages.success(
                self.request,
                f"Congratulations! You found a token: '{token.description}' "
                "- Keep hunting, there might be more tokens out there.",
            )

        else:
            messages.info(
                self.request,
                f"You already got this token. You submitted it at: {token_find.created}"
            )

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect back to dashboard on success"""
        return reverse("tokens:dashboard", kwargs={"camp_slug": self.request.camp.slug})

