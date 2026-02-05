"""All views for the Token application."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models import Exists
from django.db.models import F
from django.db.models import Min
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models.functions import TruncHour
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView
from django.views.generic import ListView
from prometheus_client import Gauge

if TYPE_CHECKING:
    from django.db.models import QuerySet

from teams.models import Team
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

    def get_queryset(self):
        """Get active tokens filtered by camp slug"""
        return self.model.objects.filter(active=True).filter(camp=self.request.camp).prefetch_related("category")

    def get_context_data(self, **kwargs):
        """Return context containing form, player-statistics, and widgets metrics"""
        context = super().get_context_data(**kwargs)
        context["game_team"] = Team.objects.filter(
            camp=self.request.camp,
            name__icontains="game"
        ).first()
        context["form"] = TokenFindSubmitForm()

        camp_finds = TokenFind.objects.filter(token__camp=self.request.camp.pk)
        player_finds = camp_finds.filter(user=self.request.user)

        context["player_stats"] = self.get_player_stats_metrics(player_finds)
        context["widgets"] = {
            "total_players": self.get_total_players_metrics(camp_finds),
            "total_finds": self.get_total_finds_metrics(camp_finds),
            "token_activity": self.get_token_activity_metrics(camp_finds),
            "token_categories": self.get_token_categories_metrics(),
            "options": {
                "camp_colour": self.request.camp.colour,
                "light_text": self.request.camp.light_text,
            },
        }

        return context

    def get_player_stats_metrics(self, player_finds: QuerySet) -> dict:
        """Return all of the metrics for player statistics"""
        player_finds_count = player_finds.count()
        tokens_count = self.object_list.count()
        return {
            "tokens_found": player_finds_count,
            "tokens_missing": tokens_count - player_finds_count,
            "tokens_count": tokens_count,
        }

    def get_total_players_metrics(self, camp_finds: QuerySet) -> dict:
        """ "Return metrics for the 'total players' widget"""
        last_joined_player = (
            User.objects.filter(
                token_finds__isnull=False,
                token_finds__token__camp=self.request.camp.pk,
            )
            .annotate(latest_find=Min("token_finds__created"))
            .order_by("latest_find")
            .last()
        )
        unique_player_count = camp_finds.distinct("user").count()
        non_player_count = self.request.camp.participant_count

        if non_player_count:  # Avoid ZeroDivisionError
            players_pct = unique_player_count / (unique_player_count + non_player_count) * 100
            non_players_pct = non_player_count / (unique_player_count + non_player_count) * 100
        else:
            players_pct = 0
            non_players_pct = 0

        return {
            "count": unique_player_count,
            "no_js": {
                "Players": {
                    "value": unique_player_count,
                    "pct": players_pct,
                },
                "Non-Players": {
                    "value": non_player_count,
                    "pct": non_players_pct,
                },
            },
            "chart": {
                "series": [unique_player_count, non_player_count],
                "labels": ["Players", "Non-players"],
            },
            "last_join_time": (last_joined_player.latest_find if last_joined_player else None),
        }

    def get_total_finds_metrics(self, camp_finds: QuerySet) -> dict:
        """Return metrics for the 'total finds' widget"""
        total_finds_count = camp_finds.distinct("token").count()
        token_count = self.object_list.count()
        latest_find = camp_finds.order_by("created").last()

        return {
            "count": camp_finds.count(),
            "latest_find": latest_find.created if latest_find else None,
            "no_js": {
                "Unique finds": {
                    "value": total_finds_count,
                    "pct": (total_finds_count / token_count) * 100 if token_count else 0,
                },
                "Not found": {
                    "value": (token_count - total_finds_count),
                    "pct": (token_count - total_finds_count) / token_count * 100 if token_count else 0,
                },
            },
            "chart": {
                "series": [
                    total_finds_count,
                    (token_count - total_finds_count),
                ],
                "labels": ["Unique finds", "Not found"],
            },
        }

    def get_token_categories_metrics(self) -> dict:
        """Return metrics for the 'token categories' widget

        Calculate the percentage of tokens found in each category by all players.
        """
        token_finds_qs = TokenFind.objects.filter(token=OuterRef("id"))
        found_tokens_qs = Token.objects.filter(camp=self.request.camp).annotate(
            was_found=Exists(token_finds_qs),
        )
        category_data = found_tokens_qs.values(category_name=F("category__name")).annotate(
            total_tokens=Count("id", distinct=True),
            found_tokens=Count("id", filter=Q(was_found=True), distinct=True),
        )

        labels, series = [], []
        for category in category_data:
            labels.append(category["category_name"])
            series.append(
                (category["found_tokens"] / category["total_tokens"]) * 100,
            )

        return {
            "count": len(labels),
            "no_js": dict(zip(labels, series, strict=False)),
            "chart": {
                "labels": labels,
                "series": series,
            },
        }

    def get_token_activity_metrics(self, camp_finds: QuerySet) -> dict:
        """Return metrics for the 'token activity' widget"""
        now = timezone.localtime()
        start = now - timezone.timedelta(hours=23)
        last_24h_qs = (
            camp_finds.filter(created__gte=start, created__lte=now)
            .annotate(hour=TruncHour("created"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )
        count_by_hours = {entry["hour"]: entry["count"] for entry in last_24h_qs}

        labels, series = [], []
        HOURS = 24
        for i in range(HOURS):
            delta = start + timedelta(hours=i)
            labels.append(delta.strftime("%H"))

            trunc_hour = delta.replace(minute=0, second=0, microsecond=0)
            series.append(count_by_hours.get(trunc_hour, 0))

        last_60m_qs = camp_finds.filter(created__gte=(now - timedelta(minutes=60)))
        no_js_series = series.copy()
        no_js_series.reverse()
        no_js_labels = labels.copy()
        no_js_labels.reverse()

        return {
            "last_60m_count": last_60m_qs.count(),
            "no_js": dict(zip(no_js_labels, no_js_series, strict=False)),
            "chart": {
                "series": series,
                "labels": labels,
            },
        }


class TokenSubmitFormView(LoginRequiredMixin, FormView):
    """View for submitting a token form"""

    form_class = TokenFindSubmitForm
    template_name = "token_submit.html"

    def dispatch(self, request, *args, **kwargs):
        """Redirect to dashboard when no tokens exist for this camp."""
        if not request.camp.token_set.all().exists():
            _kwargs = {"camp_slug": kwargs.get("camp_slug")}
            return redirect(reverse("tokens:dashboard", kwargs=_kwargs))

        return super().dispatch(request, *args, **kwargs)

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
                f"You already got this token. You submitted it at: {token_find.created}",
            )

        return redirect(self.get_success_url())

    def get_success_url(self):
        """Redirect back to dashboard on success"""
        return reverse("tokens:dashboard", kwargs={"camp_slug": self.request.camp.slug})
