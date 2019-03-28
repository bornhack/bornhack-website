from django.http import HttpResponseRedirect, Http404
from django.shortcuts import redirect, get_object_or_404

from .models import Chain, Credebtor


class ChainViewMixin(object):
    """
    The ChainViewMixin sets self.chain based on chain_slug from the URL
    """
    def setup(self, *args, **kwargs):
        if hasattr(super(), 'setup'):
            super().setup(*args, **kwargs)
        self.chain = get_object_or_404(
            Chain,
            slug=self.kwargs["chain_slug"],
        )


class CredebtorViewMixin(object):
    """
    The CredebtorViewMixin sets self.credebtor based on credebtor_slug from the URL
    """
    def setup(self, *args, **kwargs):
        if hasattr(super(), 'setup'):
            super().setup(*args, **kwargs)
        self.credebtor = get_object_or_404(
            Credebtor,
            slug=self.kwargs["credebtor_slug"],
        )


class ExpensePermissionMixin(object):
    """
    This mixin checks if request.user submitted the Expense, or if request.user has camps.economyteam_permission
    """
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.user == self.request.user or self.request.user.has_perm('camps.economyteam_permission'):
            return obj
        else:
            # the current user is different from the user who submitted the expense, and current user is not in the economy team; fuckery is afoot, no thanks
            raise Http404()


class RevenuePermissionMixin(object):
    """
    This mixin checks if request.user submitted the Revenue, or if request.user has camps.economyteam_permission
    """
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.user == self.request.user or self.request.user.has_perm('camps.economyteam_permission'):
            return obj
        else:
            # the current user is different from the user who submitted the revenue, and current user is not in the economy team; fuckery is afoot, no thanks
            raise Http404()


class ReimbursementPermissionMixin(object):
    """
    This mixin checks if request.user owns the Reimbursement, or if request.user has camps.economyteam_permission
    """
    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if obj.reimbursement_user == self.request.user or self.request.user.has_perm('camps.economyteam_permission'):
            return obj
        else:
            # the current user is different from the user who "owns" the reimbursement, and current user is not in the economy team; fuckery is afoot, no thanks
            raise Http404()

