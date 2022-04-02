import csv
import logging
from itertools import chain
from typing import Optional

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from ..mixins import InfoTeamPermissionMixin
from camps.mixins import CampViewMixin
from economy.models import Pos
from shop.models import CreditNote, Invoice, Order, OrderProductRelation
from tickets.models import (
    DiscountTicket,
    ShopTicket,
    SponsorTicket,
    TicketType,
    TicketTypeUnion,
)

from ..forms import OrderProductRelationRefundFormSet
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


class ScanTicketsPosSelectView(
    LoginRequiredMixin,
    InfoTeamPermissionMixin,
    CampViewMixin,
    ListView,
):
    model = Pos
    template_name = "scan_ticket_pos_select.html"


class ScanTicketsView(
    LoginRequiredMixin,
    InfoTeamPermissionMixin,
    CampViewMixin,
    TemplateView,
):
    template_name = "info_desk/scan.html"

    ticket = None
    order = None
    order_search = False

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.pos = Pos.objects.get(team__camp=self.camp, slug=kwargs["pos_slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["pos"] = self.pos

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
        ticket_to_check_in.mark_as_used(pos=self.pos, username=request.user)
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
        messages.success(request, f"Order #{order.id} has been marked as paid!")


class ShopTicketOverview(
    LoginRequiredMixin,
    InfoTeamPermissionMixin,
    CampViewMixin,
    ListView,
):
    model = ShopTicket
    template_name = "shop_ticket_overview.html"
    context_object_name = "shop_tickets"

    def get_context_data(self, *, object_list=None, **kwargs):
        kwargs["ticket_types"] = TicketType.objects.filter(camp=self.camp)
        return super().get_context_data(object_list=object_list, **kwargs)


################################
# ORDERS & INVOICES


class InvoiceListView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    model = Invoice
    template_name = "invoice_list.html"


class InvoiceListCSVView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    """
    CSV export of invoices for bookkeeping stuff
    """

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="bornhack-infoices-{timezone.now()}.csv"'
        writer = csv.writer(response)
        writer.writerow(["invoice", "invoice_date", "amount_dkk", "order", "paid"])
        for invoice in Invoice.objects.all().order_by("-id"):
            writer.writerow(
                [
                    invoice.id,
                    invoice.created.date(),
                    invoice.order.total
                    if invoice.order
                    else invoice.customorder.amount,
                    invoice.get_order,
                    invoice.get_order.paid,
                ],
            )
        return response


class InvoiceDownloadView(LoginRequiredMixin, DetailView):
    model = Invoice
    pk_url_kwarg = "invoice_id"

    def get(self, request, *args, **kwargs):
        if not self.get_object().pdf:
            raise Http404
        response = HttpResponse(content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = f"attachment; filename='{self.get_object().filename}'"
        response.write(self.get_object().pdf.read())
        return response


class OrderListView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    model = Order
    template_name = "order_list_backoffice.html"

    def get_queryset(self, **kwargs):
        """Preload stuff for speed."""
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "oprs__product",
                "user",
                "invoice",
                "refunds",
            )
        )


class OrderDetailView(CampViewMixin, InfoTeamPermissionMixin, DetailView):
    model = Order
    template_name = "order_detail_backoffice.html"
    pk_url_kwarg = "order_id"


class OrderRefundView(CampViewMixin, InfoTeamPermissionMixin, DetailView):
    model = Order
    template_name = "order_refund_backoffice.html"
    pk_url_kwarg = "order_id"

    def get_context_data(self, **kwargs):
        kwargs["formset"] = OrderProductRelationRefundFormSet(
            queryset=OrderProductRelation.objects.filter(order=self.get_object())
        )
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        formset = OrderProductRelationRefundFormSet(
            request.POST,
            queryset=OrderProductRelation.objects.filter(order=self.get_object()),
        )

        if not formset.is_valid():
            messages.error(
                request,
                "Some error!",
            )
            return self.render_to_response({"formset": formset})

        # get a lock for all the OPRs we are updating
        _ = (
            OrderProductRelation.objects.select_related("shoptickets")
            .filter(order=self.get_object())
            .select_for_update()
        )
        with transaction.atomic():
            for form in formset:
                opr = form.save(commit=False)
                opr.refunded += form.cleaned_data["refund_quantity"]
                opr.save()
                # TODO: Post process - delete tickets, create credit note etc.

        return HttpResponseRedirect(
            reverse("backoffice:order_list", kwargs={"camp_slug": self.camp.slug})
        )


class OrderDownloadProformaInvoiceView(LoginRequiredMixin, DetailView):
    model = Order
    pk_url_kwarg = "order_id"

    def get(self, request, *args, **kwargs):
        if not self.get_object().pdf:
            raise Http404
        response = HttpResponse(content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = f"attachment; filename='{self.get_object().filename}'"
        response.write(self.get_object().pdf.read())
        return response


class OrderUpdateView(CampViewMixin, InfoTeamPermissionMixin, UpdateView):
    model = Order
    pk_url_kwarg = "order_id"
    template_name = "order_update.html"
    fields = ["notes"]


class CreditNoteListView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    model = CreditNote
    template_name = "creditnote_list.html"
