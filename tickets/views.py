from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views.generic import CreateView, TemplateView, DetailView
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from camps.models import Camp

from .models import Ticket, TicketType
from .forms import TicketForm


class CampTicketSaleCheck(object):
    def dispatch(self, *args, **kwargs):
        current_camp = Camp.objects.current()
        if current_camp and current_camp.ticket_sale_open:
            return super(CampTicketSaleCheck, self).dispatch(*args, **kwargs)
        raise Http404()


class TicketIndexView(CampTicketSaleCheck, TemplateView):
    template_name = "tickets/index.html"

    def get_context_data(self, **kwargs):
        context = super(TicketIndexView, self).get_context_data(**kwargs)
        context['ticket_types'] = TicketType.objects.all()
        return context


class TicketDetailView(LoginRequiredMixin, CampTicketSaleCheck, DetailView):
    model = Ticket
    template_name = 'tickets/detail.html'
    context_object_name = 'ticket'


class BuyTicketView(LoginRequiredMixin, CampTicketSaleCheck, CreateView):
    model = Ticket
    template_name = "tickets/buy.html"
    form_class = TicketForm

    def get_form_kwargs(self):
        kwargs = super(BuyTicketView, self).get_form_kwargs()
        ticket_type = self.request.GET.get('ticket_type', None)
        if ticket_type:
            kwargs['initial'] = {
                'ticket_type': ticket_type
            }

        return kwargs

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.user = self.request.user
        instance.save()
        return HttpResponseRedirect(
            reverse_lazy('tickets:detail', kwargs={
                'pk': str(instance.pk)
            })
        )

