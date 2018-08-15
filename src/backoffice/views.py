import logging
from itertools import chain

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import UpdateView
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from camps.mixins import CampViewMixin
from shop.models import OrderProductRelation
from tickets.models import ShopTicket, SponsorTicket, DiscountTicket
from profiles.models import Profile
from program.models import SpeakerProposal, EventProposal

from .mixins import BackofficeViewMixin

logger = logging.getLogger("bornhack.%s" % __name__)



class InfodeskMixin(CampViewMixin, PermissionRequiredMixin):
    permission_required = ("camps.infodesk_permission")


class BackofficeIndexView(InfodeskMixin, TemplateView):
    template_name = "index.html"


class ProductHandoutView(InfodeskMixin, ListView):
    template_name = "product_handout.html"

    def get_queryset(self, **kwargs):
        return OrderProductRelation.objects.filter(
            handed_out=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False
        ).order_by('order')


class BadgeHandoutView(InfodeskMixin, ListView):
    template_name = "badge_handout.html"
    context_object_name = 'tickets'

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(badge_handed_out=False)
        sponsortickets = SponsorTicket.objects.filter(badge_handed_out=False)
        discounttickets = DiscountTicket.objects.filter(badge_handed_out=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class TicketCheckinView(InfodeskMixin, BackofficeViewMixin, ListView):
    template_name = "ticket_checkin.html"
    context_object_name = 'tickets'

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(checked_in=False)
        sponsortickets = SponsorTicket.objects.filter(checked_in=False)
        discounttickets = DiscountTicket.objects.filter(checked_in=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class ApproveNamesView(BackofficeViewMixin, ListView):
    template_name = "approve_public_credit_names.html"
    context_object_name = 'profiles'

    def get_queryset(self, **kwargs):
        return Profile.objects.filter(public_credit_name_approved=False).exclude(public_credit_name='')


class ManageProposalsView(BackofficeViewMixin, ListView):
    """
    This view shows a list of pending SpeakerProposal and EventProposals.
    """
    template_name = "manage_proposals.html"
    context_object_name = 'speakerproposals'

    def get_queryset(self, **kwargs):
        return SpeakerProposal.objects.filter(
            camp=self.camp,
            proposal_status=SpeakerProposal.PROPOSAL_PENDING
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eventproposals'] = EventProposal.objects.filter(
            track__camp=self.camp,
            proposal_status=EventProposal.PROPOSAL_PENDING
        )
        return context


class ProposalManageView(BackofficeViewMixin, UpdateView):
    """
    This class contains the shared logic between SpeakerProposalManageView and EventProposalManageView
    """
    fields = []

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        logger.debug(form.data)
        if 'approve' in form.data:
            # approve button was pressed
            form.instance.mark_as_approved(self.request)
        elif 'reject' in form.data:
            # reject button was pressed
            form.instance.mark_as_rejected(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(reverse('backoffice:manage_proposals', kwargs={'camp_slug': self.camp.slug}))


class SpeakerProposalManageView(ProposalManageView):
    """
    This view allows an admin to approve/reject SpeakerProposals
    """
    model = SpeakerProposal
    template_name = "manage_speakerproposal.html"


class EventProposalManageView(ProposalManageView):
    """
    This view allows an admin to approve/reject EventProposals
    """
    model = EventProposal
    template_name = "manage_eventproposal.html"


class MerchandiseOrdersView(BackofficeViewMixin, ListView):
    template_name = "orders_merchandise.html"

    def get_queryset(self, **kwargs):
        camp_prefix = 'BornHack {}'.format(timezone.now().year)

        return OrderProductRelation.objects.filter(
            handed_out=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
            product__category__name='Merchandise',
        ).filter(
            product__name__startswith=camp_prefix
        ).order_by('order')


class MerchandiseToOrderView(BackofficeViewMixin, TemplateView):
    template_name = "merchandise_to_order.html"

    def get_context_data(self, **kwargs):
        camp_prefix = 'BornHack {}'.format(timezone.now().year)

        order_relations = OrderProductRelation.objects.filter(
            handed_out=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
            product__category__name='Merchandise',
        ).filter(
            product__name__startswith=camp_prefix
        )

        merchandise_orders = {}
        for relation in order_relations:
            try:
                quantity = merchandise_orders[relation.product.name] + relation.quantity
                merchandise_orders[relation.product.name] = quantity
            except KeyError:
                merchandise_orders[relation.product.name] = relation.quantity

        context = super().get_context_data(**kwargs)
        context['merchandise'] = merchandise_orders
        return context


class VillageOrdersView(BackofficeViewMixin, ListView):
    template_name = "orders_village.html"

    def get_queryset(self, **kwargs):
        camp_prefix = 'BornHack {}'.format(timezone.now().year)

        return OrderProductRelation.objects.filter(
            handed_out=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
            product__category__name='Villages',
        ).filter(
            product__name__startswith=camp_prefix
        ).order_by('order')


class VillageToOrderView(BackofficeViewMixin, TemplateView):
    template_name = "village_to_order.html"

    def get_context_data(self, **kwargs):
        camp_prefix = 'BornHack {}'.format(timezone.now().year)

        order_relations = OrderProductRelation.objects.filter(
            handed_out=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
            product__category__name='Villages',
        ).filter(
            product__name__startswith=camp_prefix
        )

        village_orders = {}
        for relation in order_relations:
            try:
                quantity = village_orders[relation.product.name] + relation.quantity
                village_orders[relation.product.name] = quantity
            except KeyError:
                village_orders[relation.product.name] = relation.quantity

        context = super().get_context_data(**kwargs)
        context['village'] = village_orders
        return context

