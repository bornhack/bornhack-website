from __future__ import annotations

import csv
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from backoffice.forms import InvoiceDownloadForm
from backoffice.forms import ShopTicketRefundFormSet
from backoffice.forms import TicketGroupRefundFormSet
from backoffice.mixins import EconomyTeamPermissionMixin
from backoffice.mixins import InfoTeamPermissionMixin
from camps.mixins import CampViewMixin
from economy.models import Pos
from shop.forms import RefundForm
from shop.models import CreditNote
from shop.models import Invoice
from shop.models import Order
from shop.models import OrderProductRelation
from shop.models import Refund
from tickets.models import PrizeTicket
from tickets.models import ShopTicket
from tickets.models import SponsorTicket
from tickets.models import TicketType
from tickets.models import TicketTypeUnion
from utils.mixins import GetObjectMixin

logger = logging.getLogger(f"bornhack.{__name__}")


def _ticket_getter_by_token(token) -> TicketTypeUnion | None:
    for ticket_class in [ShopTicket, SponsorTicket, PrizeTicket]:
        try:
            return ticket_class.objects.get(Q(token=token) | Q(badge_token=token))
        except ticket_class.DoesNotExist:
            continue
    return None


def _ticket_getter_by_pk(pk):
    for ticket_class in [ShopTicket, SponsorTicket, PrizeTicket]:
        try:
            return ticket_class.objects.get(pk=pk)
        except ticket_class.DoesNotExist:
            pass
    return None


class ScanTicketsPosSelectView(
    LoginRequiredMixin,
    InfoTeamPermissionMixin,
    CampViewMixin,
    ListView,
):
    """Class for the ticket scan index view."""

    model = Pos
    template_name = "scan_ticket_pos_select.html"

    def dispatch(self, *args, **kwargs):
        """Method for preventing changes to read-only camps."""
        if self.camp.read_only:
            return HttpResponseForbidden("Camp is read-only")
        return super().dispatch(*args, **kwargs)


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

    def dispatch(self, *args, **kwargs):
        """Method for preventing changes to read-only camps."""
        if self.camp.read_only:
            return HttpResponseForbidden("Camp is read-only")
        return super().dispatch(*args, **kwargs)

    def setup(self, *args, **kwargs) -> None:
        super().setup(*args, **kwargs)
        self.pos = Pos.objects.get(team__camp=self.camp, slug=kwargs["pos_slug"])

    def get_context_data(self, **kwargs):
        """Method for loading the page data."""
        context = super().get_context_data(**kwargs)

        context["pos"] = self.pos

        if self.ticket:
            context["ticket"] = self.ticket

        elif "ticket_token" in self.request.POST:
            # Slice to get rid of the first character which is a '#'
            ticket_token = self.request.POST.get("ticket_token")[1:]

            ticket: TicketTypeUnion | None = _ticket_getter_by_token(ticket_token)

            if ticket:
                context["ticket"] = ticket
                context["is_badge"] = ticket_token == ticket.badge_token
            else:
                messages.warning(self.request, "Ticket not found!")

        elif self.order_search:
            context["order"] = self.order
            if self.order:
                context["tickets"] = self.order.get_tickets()

        return context

    def _set_order(self) -> None:
        self.order_search = True
        try:
            order_id = self.request.POST.get("find_order_id")
            self.order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            pass

    def post(self, request, **kwargs):
        if "check_in_ticket_id" in request.POST:
            self.ticket = self.check_in_ticket(request)
            if "find_order_id" in self.request.POST:
                self._set_order()
                self.ticket = None
        elif "badge_ticket_id" in request.POST:
            self.ticket = self.hand_out_badge(request)
        elif "find_order_id" in request.POST:
            self._set_order()
        elif "mark_as_paid" in request.POST:
            self.mark_order_as_paid(request)

        return super().get(request, **kwargs)

    def check_in_ticket(self, request):
        check_in_ticket_id = request.POST.get("check_in_ticket_id")
        ticket_to_check_in = _ticket_getter_by_pk(check_in_ticket_id)
        ticket_to_check_in.mark_as_used(pos=self.pos, user=request.user)
        messages.info(request, "Ticket checked-in!")
        return ticket_to_check_in

    def hand_out_badge(self, request):
        badge_ticket_id = request.POST.get("badge_ticket_id")
        ticket_to_handout_badge_for = _ticket_getter_by_pk(badge_ticket_id)
        ticket_to_handout_badge_for.badge_handed_out = True
        ticket_to_handout_badge_for.save()
        messages.info(request, "Badge marked as handed out!")
        return ticket_to_handout_badge_for

    def mark_order_as_paid(self, request) -> None:
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
        """Method for loading the page data."""
        kwargs["ticket_types"] = TicketType.objects.filter(camp=self.camp)
        return super().get_context_data(object_list=object_list, **kwargs)


class ScanInventoryView(
    LoginRequiredMixin,
    InfoTeamPermissionMixin,
    CampViewMixin,
    TemplateView,
):
    """Class for checking in inventory."""

    template_name = "info_desk/inventory.html"

    opr: None | OrderProductRelation = None

    def dispatch(self, *args, **kwargs):
        """Method for preventing changes to read-only camps."""
        if self.camp.read_only:
            return HttpResponseForbidden("Camp is read-only")
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Method for loading the page data."""
        context = super().get_context_data(**kwargs)

        context["pos"] = Pos.objects.get(team__camp=self.camp, slug=kwargs["pos_slug"])

        if "token" in self.request.POST:
            context["failed"] = False
            # Slice to get rid of the first character which is a '#'
            try:
                search_token = self.request.POST.get("token")[1:].split("/")
                token_type = search_token[2]
                token_id = int(search_token[3])
            except IndexError:
                self.opr = None
                context["failed"] = True
                return context
            token_action = None
            if len(search_token) == 5:
                token_action = search_token[4]
            if token_type == "opr" and not token_action:
                try:
                    self.opr = OrderProductRelation.objects.get(id=token_id)
                except OrderProductRelation.DoesNotExist:
                    self.opr = None
                    context["failed"] = True
                context["opr"] = self.opr

        return context

    def post(self, request, **kwargs):
        """Method for saving the checkin."""
        try:
            search_token = self.request.POST.get("token")[1:].split("/")
            token_type = search_token[2]
            token_id = int(search_token[3])
        except IndexError:
            messages.error(
                self.request,
                "Not found.",
            )
            return super().get(request, **kwargs)
        token_action = None
        if len(search_token) == 5:
            token_action = search_token[4]
        if token_type == "opr" and token_action == "checkin":
            self.opr = OrderProductRelation.objects.get(id=token_id)
            self.opr.ready_for_pickup = True
            self.opr.save()
            messages.success(
                self.request,
                "Item checked in.",
            )
        return super().get(request, **kwargs)


class ScanInventoryIndexView(
    LoginRequiredMixin,
    InfoTeamPermissionMixin,
    CampViewMixin,
    ListView,
):
    """View for selecting the POS location for check-in of items."""

    model = Pos
    template_name = "info_desk/inventory_index.html"

    def dispatch(self, *args, **kwargs):
        """Method for preventing changes on read-only camp."""
        if self.camp.read_only:
            return HttpResponseForbidden("Camp is read-only")
        return super().dispatch(*args, **kwargs)


################################
# ORDERS & INVOICES


class InvoiceListView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    model = Invoice
    template_name = "invoice_list.html"


class InvoiceDownloadMultipleView(CampViewMixin, EconomyTeamPermissionMixin, FormView):
    model = Invoice
    template_name = "invoice_download.html"
    form_class = InvoiceDownloadForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["invoices"] = []
        return context

    def form_valid(self, form):
        orders = form.cleaned_data["orders"]
        invoices = form.cleaned_data["invoices"]
        filtered_invoices = Invoice.objects.filter(
            Q(id__in=invoices) | Q(order__id__in=orders),
        )
        context = self.get_context_data()
        context["invoices"] = list(filtered_invoices.values("id"))
        for invoice in context["invoices"]:
            invoice["url"] = reverse(
                "backoffice:invoice_download",
                kwargs={"camp_slug": self.camp.slug, "invoice_id": invoice["id"]},
            )
        return render(self.request, self.template_name, context)


class InvoiceListCSVView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    """CSV export of invoices for bookkeeping stuff."""

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="bornhack-infoices-{timezone.now()}.csv"'
        writer = csv.writer(response)
        writer.writerow(["invoice", "invoice_date", "amount_dkk", "order", "paid"])
        for invoice in Invoice.objects.all().order_by("-id"):
            writer.writerow(
                [
                    invoice.id,
                    invoice.created.date(),
                    (invoice.order.total if invoice.order else invoice.customorder.amount),
                    invoice.get_order,
                    invoice.get_order.paid,
                ],
            )
        return response


class InvoiceDownloadView(LoginRequiredMixin, InfoTeamPermissionMixin, DetailView):
    model = Invoice
    pk_url_kwarg = "invoice_id"

    def get(self, request, *args, **kwargs):
        if not self.get_object().pdf:
            raise Http404
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={self.get_object().filename}"
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
                "products",
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


class OrderUpdateView(CampViewMixin, InfoTeamPermissionMixin, UpdateView):
    model = Order
    pk_url_kwarg = "order_id"
    template_name = "order_update.html"
    fields = ["notes"]

    def form_valid(self, form):
        messages.info(request=self.request, message=f"Order #{self.object.id} updated!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("backoffice:order_list", kwargs={"camp_slug": self.camp.slug})


class OrderDownloadProformaInvoiceView(
    LoginRequiredMixin,
    InfoTeamPermissionMixin,
    DetailView,
):
    model = Order
    pk_url_kwarg = "order_id"

    def get(self, request, *args, **kwargs):
        if not self.get_object().pdf:
            raise Http404
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename='{self.get_object().filename}'"
        response.write(self.get_object().pdf.read())
        return response


################################
# REFUNDS & CREDITNOTES


class RefundListView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    model = Refund
    template_name = "refund_list_backoffice.html"


class RefundDetailView(CampViewMixin, InfoTeamPermissionMixin, DetailView):
    model = Refund
    template_name = "refund_detail_backoffice.html"
    pk_url_kwarg = "refund_id"


class RefundUpdateView(CampViewMixin, InfoTeamPermissionMixin, UpdateView):
    model = Refund
    template_name = "refund_update_backoffice.html"
    fields = ["paid", "notes"]
    pk_url_kwarg = "refund_id"

    def get_success_url(self):
        return reverse("backoffice:refund_list", kwargs={"camp_slug": self.camp.slug})


class OrderRefundView(
    GetObjectMixin,
    CampViewMixin,
    InfoTeamPermissionMixin,
    DetailView,
):
    model = Order
    template_name = "order_refund_backoffice.html"
    pk_url_kwarg = "order_id"

    def get_context_data(self, **kwargs):
        kwargs["oprs"] = {}
        kwargs["ticket_groups"] = {}
        for opr in self.get_object().oprs.all():
            if opr.product.sub_products.exists():
                kwargs["ticket_groups"][opr] = TicketGroupRefundFormSet(
                    queryset=opr.ticketgroups.annotate_ticket_info(),
                    prefix=f"ticket-group-{opr.id}",
                )
            else:
                kwargs["oprs"][opr] = ShopTicketRefundFormSet(
                    queryset=opr.unused_shoptickets,
                    prefix=f"ticket-{opr.id}",
                )
        kwargs["refund_form"] = RefundForm()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        # lock all the OPRS we are updating
        oprs = (
            OrderProductRelation.objects.prefetch_related("shoptickets")
            .filter(order=self.get_object())
            .select_for_update()
        )

        opr_dict = {}
        tickets_to_delete = []
        with transaction.atomic():
            for opr in oprs:
                # Do not include fully refunded oprs
                if not opr.possible_refund:
                    continue

                if not opr.product.sub_products.exists():
                    ticket_formset = ShopTicketRefundFormSet(
                        request.POST,
                        queryset=opr.unused_shoptickets,
                        prefix=f"ticket-{opr.id}",
                    )

                    if not ticket_formset.is_valid():
                        messages.error(
                            request,
                            "Some error!",
                        )
                        return self.get(request, *args, **kwargs)

                    for form in ticket_formset:
                        refund = form.cleaned_data["refund"]
                        ticket: ShopTicket = form.cleaned_data["uuid"]
                        if isinstance(ticket, str):
                            ticket = ShopTicket.objects.get(uuid=ticket)
                        if refund:
                            tickets_to_delete.append(ticket.pk)
                            if opr in opr_dict:
                                opr_dict[opr] += 1
                            else:
                                opr_dict[opr] = 1
                else:
                    # The OPR points at a bundle
                    ticket_group_formset = TicketGroupRefundFormSet(
                        request.POST,
                        queryset=opr.ticketgroups.all(),
                        prefix=f"ticket-group-{opr.id}",
                    )

                    if not ticket_group_formset.is_valid():
                        messages.error(
                            request,
                            "Some error!",
                        )
                        return self.get(request, *args, **kwargs)

                    for form in ticket_group_formset:
                        refund = form.cleaned_data["refund"]
                        ticket_group = form.cleaned_data["uuid"]
                        if refund:
                            tickets_to_delete += list(
                                ticket_group.tickets.values_list("pk", flat=True),
                            )
                            # TODO: ... this is not correct, but it's a start
                            if opr in opr_dict:
                                opr_dict[opr] += 1
                            else:
                                opr_dict[opr] = 1

                refund_form = RefundForm(request.POST)

            if not opr_dict:
                messages.error(request, "Nothing to refund!")
                context = self.get_context_data()
                context["refund_form"] = refund_form
                return self.render_to_response(context)

            if opr_dict and refund_form.is_valid():
                refund = refund_form.save(commit=False)
                refund.order = self.get_object()
                refund.created_by = request.user
                refund.save()

                for opr, quantity in opr_dict.items():
                    opr.create_rpr(refund=refund, quantity=quantity)

            ShopTicket.objects.filter(pk__in=tickets_to_delete).delete()

            messages.success(
                self.request,
                f"Refund {refund.id} created, {len(tickets_to_delete)} tickets deleted.",
            )
            return HttpResponseRedirect(
                reverse(
                    "backoffice:refund_detail",
                    kwargs={"camp_slug": self.camp.slug, "refund_id": refund.id},
                ),
            )


class CreditNoteListView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    model = CreditNote
    template_name = "creditnote_list_backoffice.html"


class CreditNoteDownloadView(LoginRequiredMixin, InfoTeamPermissionMixin, DetailView):
    model = CreditNote
    pk_url_kwarg = "credit_note_id"

    def get(self, request, *args, **kwargs):
        if not self.get_object().pdf:
            raise Http404
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={self.get_object().filename}"
        response.write(self.get_object().pdf.read())
        return response
