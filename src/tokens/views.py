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

from django.db.models import F, ExpressionWrapper, DurationField, Avg, Window
from django.db.models.functions import Lead

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

        camp_finds = TokenFind.objects.filter(token__camp=self.request.camp.pk)
        user_finds = camp_finds.filter(user=self.request.user)
        context["user_finds"] = user_finds

        context["active_camp_tokens"] = self.object_list
        context["user_finds_missing"] = len(self.object_list) - len(user_finds)

        context["widget_total_players"] = {
            "count": camp_finds.distinct("user").count(),
            "last_join": self.last_player_join()
        }

        token_finds_count = camp_finds.distinct("token").count()
        found_pct = (token_finds_count / self.object_list.count()) * 100
        context["widget_tokens_found"] = {
            "count": camp_finds.count(),
            "last_found": self.last_token_find(camp_finds),
            "found_pct": f"{found_pct:.1f}",
            "not_found_pct": f"{(100 - found_pct):.1f}",
        }
        context["widget_avg_find_time"] = {
            "avg_find_time": self.avg_find_time(camp_finds),
            "users_avg_find_time": self.user_avg_find_time(user_finds),
        }

        return context

    def last_player_join(self) -> int:
        """
        Return the time in minutes since the last player joined the game
        by submitting its first token find.
        """
        last_player_join = (
            User.objects.filter(
                token_finds__isnull = False,
                token_finds__token__camp = self.request.camp.pk
            )
            .annotate(latest_find=Min("token_finds__created"))
            .order_by("latest_find").last().latest_find
        )
        delta = timezone.now() - last_player_join
        return int(delta.total_seconds() // 60)

    def last_token_find(self, camp_finds: QuerySet) -> int:
        """Return the time delta in minutes for the last token submitted"""
        last_found = camp_finds.order_by("created").last()
        delta = timezone.now() - last_found.created
        return int(delta.total_seconds() // 60)

    def avg_find_time(self, camp_finds: QuerySet) -> int:
        """Calculate the average find time for all players"""
        avg_time = self._get_avg_time_between_creations(camp_finds)
        if avg_time:
            return int(avg_time.total_seconds() // 60)
        return 0

    def user_avg_find_time(self, user_finds: QuerySet) -> int:
        """Calculate the average find time in minutes for requesting user"""
        avg_time = self._get_avg_time_between_creations(user_finds)
        if avg_time:
            return int(avg_time.total_seconds() // 60)
        return 0

    def _get_avg_time_between_creations(self, qs: QuerySet):
        intervals = qs.annotate(
            next_created=Window(
                expression=Lead('created'),
                order_by=F('created').asc()
            )
        ).annotate(
            interval=ExpressionWrapper(
                F('next_created') - F('created'),
                output_field=DurationField()
            )
        ).exclude(
            next_created__isnull=True
        )

        avg = intervals.aggregate(avg_interval=Avg('interval'))['avg_interval']
        return avg

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

