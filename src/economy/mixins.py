from __future__ import annotations

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse

from .models import Chain
from .models import Credebtor


class ChainViewMixin:
    """The ChainViewMixin sets self.chain based on chain_slug from the URL."""

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)
        self.chain = get_object_or_404(Chain, slug=self.kwargs["chain_slug"])


class CredebtorViewMixin(ChainViewMixin):
    """The CredebtorViewMixin sets self.credebtor based on credebtor_slug from the URL."""

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)
        self.credebtor = get_object_or_404(
            Credebtor,
            chain=self.chain,
            slug=self.kwargs["credebtor_slug"],
        )


class ExpensePermissionMixin:
    """This mixin checks if request.user submitted the Expense, or if request.user has camps.economyteam_permission."""

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.user == self.request.user or self.request.user.has_perm(
            "camps.economyteam_permission",
        ):
            return obj
        # the current user is different from the user who submitted the expense, and current user is not in the economy team; fuckery is afoot, no thanks
        raise Http404


class RevenuePermissionMixin:
    """This mixin checks if request.user submitted the Revenue, or if request.user has camps.economyteam_permission."""

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.user == self.request.user or self.request.user.has_perm(
            "camps.economyteam_permission",
        ):
            return obj
        # the current user is different from the user who submitted the revenue, and current user is not in the economy team; fuckery is afoot, no thanks
        raise Http404


class ReimbursementPermissionMixin:
    """This mixin checks if request.user owns the Reimbursement, or if request.user has camps.economyteam_permission."""

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.reimbursement_user == self.request.user or self.request.user.has_perm(
            "camps.economyteam_permission",
        ):
            return obj
        # the current user is different from the user who "owns" the reimbursement, and current user is not in the economy team; fuckery is afoot, no thanks
        raise Http404


class ReimbursementUnpaidMixin:
    def get(self, request, *args, **kwargs):
        if self.get_object().paid:
            messages.error(
                request,
                "This reimbursement has already been paid so it cannot be modified or deleted.",
            )
            return redirect(
                reverse(
                    "economy:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                ),
            )
        # continue with the request
        return super().get(request, *args, **kwargs)
