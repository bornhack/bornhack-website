import logging
from itertools import chain
from typing import Optional

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from camps.mixins import CampViewMixin
from shop.models import Order, OrderProductRelation
from tickets.models import (
    DiscountTicket,
    ShopTicket,
    SponsorTicket,
    TicketType,
    TicketTypeUnion,
)

from ..mixins import InfoTeamPermissionMixin

logger = logging.getLogger("bornhack.%s" % __name__)


class ProductHandoutView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "product_handout.html"

    def get_queryset(self, **kwargs):
        return OrderProductRelation.objects.filter(
            ticket_generated=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
        ).order_by("order")


class BadgeHandoutView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "badge_handout.html"
    context_object_name = "tickets"

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(badge_ticket_generated=False)
        sponsortickets = SponsorTicket.objects.filter(badge_ticket_generated=False)
        discounttickets = DiscountTicket.objects.filter(badge_ticket_generated=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class TicketCheckinView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "ticket_checkin.html"
    context_object_name = "tickets"

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(used=False)
        sponsortickets = SponsorTicket.objects.filter(used=False)
        discounttickets = DiscountTicket.objects.filter(used=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


def _ticket_getter_by_token(token) -> Optional[TicketTypeUnion]:
    for ticket_class in [ShopTicket, SponsorTicket, DiscountTicket]:
        try:
            return ticket_class.objects.get(Q(token=token) | Q(badge_token=token))
        except ticket_class.DoesNotExist:
            continue


def _ticket_getter_by_pk(pk):
    for ticket_class in [ShopTicket, SponsorTicket, DiscountTicket]:
        try:
            return ticket_class.objects.get(pk=pk)
        except ticket_class.DoesNotExist:
            pass


class ScanTicketsView(
    LoginRequiredMixin, InfoTeamPermissionMixin, CampViewMixin, TemplateView
):
    template_name = "info_desk/scan.html"

    ticket = None
    order = None
    order_search = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.ticket:
            context["ticket"] = self.ticket

        elif "ticket_token" in self.request.POST:

            # Slice to get rid of the first character which is a '#'
            ticket_token = self.request.POST.get("ticket_token")[1:]

            ticket: Optional[TicketTypeUnion] = _ticket_getter_by_token(ticket_token)

            if ticket:
                context["ticket"] = ticket
                context["is_badge"] = ticket_token == ticket.badge_token
            else:
                messages.warning(self.request, "Ticket not found!")

        elif self.order_search:
            context["order"] = self.order

        return context

    def post(self, request, **kwargs):
        if "check_in_ticket_id" in request.POST:
            self.ticket = self.check_in_ticket(request)
        elif "badge_ticket_id" in request.POST:
            self.ticket = self.hand_out_badge(request)
        elif "find_order_id" in request.POST:
            self.order_search = True
            try:
                order_id = self.request.POST.get("find_order_id")
                self.order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                pass
        elif "mark_as_paid" in request.POST:
            self.mark_order_as_paid(request)

        return super().get(request, **kwargs)

    def check_in_ticket(self, request):
        check_in_ticket_id = request.POST.get("check_in_ticket_id")
        ticket_to_check_in = _ticket_getter_by_pk(check_in_ticket_id)
        ticket_to_check_in.used = True
        ticket_to_check_in.used_time = timezone.now()
        ticket_to_check_in.save()
        messages.info(request, "Ticket checked-in!")
        return ticket_to_check_in

    def hand_out_badge(self, request):
        badge_ticket_id = request.POST.get("badge_ticket_id")
        ticket_to_handout_badge_for = _ticket_getter_by_pk(badge_ticket_id)
        ticket_to_handout_badge_for.badge_handed_out = True
        ticket_to_handout_badge_for.save()
        messages.info(request, "Badge marked as handed out!")
        return ticket_to_handout_badge_for

    def mark_order_as_paid(self, request):
        order = Order.objects.get(id=request.POST.get("mark_as_paid"))
        order.mark_as_paid()
        messages.success(request, "Order #{} has been marked as paid!".format(order.id))


class ShopTicketOverview(
    LoginRequiredMixin, InfoTeamPermissionMixin, CampViewMixin, ListView
):
    model = ShopTicket
    template_name = "shop_ticket_overview.html"
    context_object_name = "shop_tickets"

    def get_context_data(self, *, object_list=None, **kwargs):
        kwargs["ticket_types"] = TicketType.objects.filter(camp=self.camp)
        return super().get_context_data(object_list=object_list, **kwargs)
