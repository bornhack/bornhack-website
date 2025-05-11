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

from .models import ShopTicket

logger = logging.getLogger("bornhack.%s" % __name__)


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
        "tickets": (base_queryset.filter(ticket_group__isnull=True)),
        "tickets_in_groups": (base_queryset.filter(ticket_group__isnull=False).order_by("ticket_group")),
    }

    return render(request, "tickets/ticket_list.html", context)


class ShopTicketDownloadView(LoginRequiredMixin, SingleObjectMixin, View):
    model = ShopTicket

    def dispatch(self, request, *args, **kwargs):
        if not request.user == self.get_object().opr.order.user:
            raise Http404("Ticket not found")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="{self.get_object().shortname}_ticket_{self.get_object().pk}.pdf"'
        )
        response.write(self.get_object().generate_pdf().getvalue())
        return response


class ShopTicketDetailView(LoginRequiredMixin, UpdateView, DetailView):
    model = ShopTicket
    template_name = "tickets/ticket_detail.html"
    context_object_name = "ticket"
    fields = ["name", "email"]

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
