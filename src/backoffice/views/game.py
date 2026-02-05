from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView

from backoffice.mixins import RaisePermissionRequiredMixin
from camps.mixins import CampViewMixin
from tokens.models import Token
from tokens.models import TokenCategory
from tokens.models import TokenFind

logger = logging.getLogger(f"bornhack.{__name__}")


################################
# Secret Token views


class TokenListView(CampViewMixin, RaisePermissionRequiredMixin, ListView):
    """Show a list of secret tokens for this camp."""

    permission_required = "camps.game_team_member"
    model = Token
    template_name = "token_list.html"


class TokenDetailView(CampViewMixin, RaisePermissionRequiredMixin, DetailView):
    """Show details for a token."""

    permission_required = "camps.game_team_member"
    model = Token
    template_name = "token_detail.html"


class TokenCreateView(CampViewMixin, RaisePermissionRequiredMixin, CreateView):
    """Create a new Token."""

    permission_required = "camps.game_team_member"
    model = Token
    template_name = "token_form.html"
    fields = ["token", "category", "hint", "description", "active", "valid_when"]

    def form_valid(self, form):
        token = form.save(commit=False)
        token.camp = self.camp
        token.save()
        return redirect(
            reverse(
                "backoffice:token_detail",
                kwargs={"camp_slug": self.camp.slug, "pk": token.id},
            ),
        )


class TokenUpdateView(CampViewMixin, RaisePermissionRequiredMixin, UpdateView):
    """Update a token."""

    permission_required = "camps.game_team_member"
    model = Token
    template_name = "token_form.html"
    fields = ["token", "category", "hint", "description", "active", "valid_when"]


class TokenDeleteView(CampViewMixin, RaisePermissionRequiredMixin, DeleteView):
    """Delete a token."""

    permission_required = "camps.game_team_member"
    model = Token
    template_name = "token_delete.html"

    def delete(self, *args, **kwargs):
        self.get_object().tokenfind_set.all().delete()
        return super().delete(*args, **kwargs)

    def get_success_url(self):
        messages.success(
            self.request,
            "The Token and all related TokenFinds has been deleted",
        )
        return reverse("backoffice:token_list", kwargs={"camp_slug": self.camp.slug})


class TokenStatsView(CampViewMixin, RaisePermissionRequiredMixin, ListView):
    """Show stats for token finds for this camp."""

    permission_required = "camps.game_team_member"
    model = User
    template_name = "token_stats.html"

    def get_queryset(self, **kwargs):
        tokenusers = TokenFind.objects.filter(token__camp=self.camp).distinct("user").values_list("user", flat=True)
        last_token_find_subquery = (
            TokenFind.objects.filter(
                user=OuterRef("pk"),
                token__camp=self.camp,
            )
            .order_by("-created")
            .values("created")[:1]
        )
        return (
            User.objects.filter(id__in=tokenusers)
            .annotate(
                token_find_count=Count(
                    "token_finds",
                    filter=Q(token_finds__token__camp=self.camp),
                ),
                last_token_find=Subquery(last_token_find_subquery),
            )
            .exclude(token_find_count=0)
        )


class TokenCategoryListView(CampViewMixin, RaisePermissionRequiredMixin, ListView):
    """Show list of token categories"""

    permission_required = "camps.game_team_member"
    model = TokenCategory
    template_name = "token_category_list.html"

    def get_queryset(self):
        """
        Get all Categories and annotate count of tokens for the current camp.
        """
        camp_tokens = Count("token", filter=Q(token__camp=self.request.camp))
        return TokenCategory.objects.annotate(token_count=camp_tokens)


class TokenCategoryCreateView(CampViewMixin, RaisePermissionRequiredMixin, CreateView):
    """Create a new token category."""

    permission_required = "camps.game_team_member"
    model = TokenCategory
    template_name = "token_category_form.html"
    fields = ["name", "description"]

    def get_success_url(self):
        messages.success(
            self.request,
            f"{self.object.name} was created successfully",
        )
        if "_addanother" in self.request.POST:
            return reverse("backoffice:token_category_create", kwargs=self.kwargs)
        if "_addtoken" in self.request.POST:
            return reverse("backoffice:token_create", kwargs=self.kwargs)
        return reverse("backoffice:token_category_list", kwargs=self.kwargs)


class TokenCategoryDetailView(CampViewMixin, RaisePermissionRequiredMixin, DetailView):
    """Show details for a token category."""

    permission_required = "camps.game_team_member"
    model = TokenCategory
    template_name = "token_category_detail.html"

    def get_context_data(self, **kwargs):
        """Add all category tokens for the current camp to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            "category_tokens": Token.objects.filter(
                category=self.object,
                camp=self.request.camp
            )
        })
        return context


class TokenCategoryDeleteView(CampViewMixin, RaisePermissionRequiredMixin, DeleteView):
    """Delete a token category"""

    permission_required = "camps.game_team_member"
    model = TokenCategory
    template_name = "token_category_delete.html"

    def get_success_url(self):
        """Return to category list after deletion"""
        messages.success(
            self.request,
            "The Token category has been deleted",
        )
        return reverse(
            "backoffice:token_category_list",
            kwargs={"camp_slug": self.camp.slug},
        )


class TokenCategoryUpdateView(CampViewMixin, RaisePermissionRequiredMixin, UpdateView):
    """Update a token category."""

    permission_required = "camps.game_team_member"
    model = TokenCategory
    template_name = "token_category_form.html"
    fields = ["name", "description"]

    def get_success_url(self):
        messages.success(
            self.request,
            f"{self.object.name} was updated successfully",
        )
        return reverse(
            "backoffice:token_category_list",
            kwargs={"camp_slug": self.camp.slug},
        )
