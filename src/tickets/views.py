import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.views.generic import DetailView, ListView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from .models import ShopTicket

logger = logging.getLogger("bornhack.%s" % __name__)


class ShopTicketListView(LoginRequiredMixin, ListView):
    model = ShopTicket
    template_name = "tickets/ticket_list.html"
    context_object_name = "tickets"

    def get_queryset(self):
        tickets = super(ShopTicketListView, self).get_queryset()
        user = self.request.user
        return tickets.filter(opr__order__user=user).order_by("ticket_type__camp")


class ShopTicketDownloadView(LoginRequiredMixin, SingleObjectMixin, View):
    model = ShopTicket

    def dispatch(self, request, *args, **kwargs):
        if not request.user == self.get_object().opr.order.user:
            raise Http404("Ticket not found")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="{type}_ticket_{pk}.pdf"'.format(
            type=self.get_object().shortname, pk=self.get_object().pk
        )
        response.write(self.get_object().generate_pdf().getvalue())
        return response


class ShopTicketDetailView(LoginRequiredMixin, UpdateView, DetailView):
    model = ShopTicket
    template_name = "tickets/ticket_detail.html"
    context_object_name = "ticket"
    fields = ["name", "email"]

    def form_valid(self, form):
        messages.info(self.request, "Ticket updated!")
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        ticket = self.get_object()
        if ticket.opr.order.user != request.user:
            raise Http404("Ticket not found")
        return super().dispatch(request, *args, **kwargs)
