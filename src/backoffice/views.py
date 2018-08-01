import logging
from itertools import chain

from django.views.generic import TemplateView, ListView
from django.views.generic.edit import UpdateView
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

from shop.models import OrderProductRelation
from tickets.models import ShopTicket, SponsorTicket, DiscountTicket
from profiles.models import Profile
from program.models import SpeakerProposal, EventProposal

from .mixins import BackofficeViewMixin

logger = logging.getLogger("bornhack.%s" % __name__)


class BackofficeIndexView(BackofficeViewMixin, TemplateView):
    template_name = "index.html"


class ProductHandoutView(BackofficeViewMixin, ListView):
    template_name = "product_handout.html"

    def get_queryset(self, **kwargs):
        return OrderProductRelation.objects.filter(
            handed_out=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False
        ).order_by('order')


class BadgeHandoutView(BackofficeViewMixin, ListView):
    template_name = "badge_handout.html"
    context_object_name = 'tickets'

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(badge_handed_out=False)
        sponsortickets = SponsorTicket.objects.filter(badge_handed_out=False)
        discounttickets = DiscountTicket.objects.filter(badge_handed_out=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class TicketCheckinView(BackofficeViewMixin, ListView):
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

