from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.generic import DetailView
from django.views.generic import UpdateView
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from utils.models import CampReadOnlyModeError

from .models import ShopTicket, PrizeTicket

logger = logging.getLogger(f"bornhack.{__name__}")


@login_required
def shop_ticket_list_view(request: HttpRequest) -> HttpResponse:
    """List all tickets for the logged-in user."""
    base_queryset = (
        ShopTicket.objects.select_related(
            "ticket_type",
            "ticket_type__camp",
            "product",
            "product__ticket_type__camp",
            "bundle_product",
        )
        .filter(opr__order__user=request.user)
        .order_by("ticket_type__camp", "ticket_group")
    )

    context = {
        "prize_tickets": PrizeTicket.objects.filter(user=request.user).order_by("ticket_type__camp"),
        "tickets": (base_queryset.filter(ticket_group__isnull=True)),
        "tickets_in_groups": (base_queryset.filter(ticket_group__isnull=False).order_by("ticket_group")),
    }

    return render(request, "tickets/ticket_list.html", context)


class TicketDownloadView(LoginRequiredMixin, SingleObjectMixin, View):
    """This view makes it possible to download ShopTickets and PrizeTickets."""
    model = ShopTicket

    def get_object(self, *args, **kwargs):
        print(kwargs)
        pk = kwargs["pk"]
        try:
            return ShopTicket.objects.get(pk=pk, opr__order__user=self.request.user)
        except ShopTicket.DoesNotExist:
            pass
        try:
            return PrizeTicket.objects.get(pk=pk, user=self.request.user)
        except PrizeTicket.DoesNotExist:
            raise Http404("Ticket not found")

    def get(self, request, *args, **kwargs):
        ticket = self.get_object(*args, **kwargs)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="BornHack_{ticket.ticket_type.camp.camp.lower.year}_{ticket.shortname}_ticket_{ticket.pk}.pdf"'
        )
        response.write(ticket.generate_pdf().getvalue())
        return response


class ShopTicketDetailView(LoginRequiredMixin, UpdateView, DetailView):
    model = ShopTicket
    template_name = "tickets/ticket_detail.html"
    context_object_name = "ticket"
    fields = ["name"]

    def form_valid(self, form):
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        ticket = self.get_object()
        if ticket.opr.order.user != request.user:
            raise Http404("Ticket not found")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except CampReadOnlyModeError:
            messages.error(
                self.request,
                "The camp is over. You can't update the ticket.",
            )
            return redirect(self.get_object().get_absolute_url())
        else:
            messages.info(self.request, "Ticket updated!")
            return response
