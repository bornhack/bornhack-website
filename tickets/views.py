import hashlib

from django.http import HttpResponseRedirect, Http404
from django.views.generic import CreateView, TemplateView, DetailView, View
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse

from camps.models import Camp

from .models import Ticket, TicketType, EpayPayment, EpayCallback
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


class TicketOrderView(LoginRequiredMixin, CampTicketSaleCheck, CreateView):
    model = Ticket
    template_name = "tickets/order.html"
    form_class = TicketForm

    def get_form_kwargs(self):
        kwargs = super(TicketOrderView, self).get_form_kwargs()
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

        if instance.payment_method == Ticket.ALTCOIN:
            return HttpResponse('Altcoin')

        if instance.payment_method == Ticket.CREDIT_CARD:
            return HttpResponseRedirect(
                reverse_lazy('tickets:epay_form', kwargs={
                    'ticket_id': str(instance.pk)
                })
            )

        return HttpResponseRedirect(
            reverse_lazy('tickets:detail', kwargs={
                'pk': str(instance.pk)
            })
        )


class EpayView(TemplateView):
    template_name = 'tickets/epay_form.html'

    def get_context_data(self, **kwargs):
        ticket = Ticket.objects.get(pk=kwargs.get('ticket_id'))
        accept_url = ticket.get_absolute_url()
        amount = ticket.ticket_type.price * 100
        order_id = str(ticket.pk)
        description = str(ticket.user.pk)

        hashstring = (
            '{merchantnumber}{description}11{amount}DKK'
            '{order_id}{accept_url}{md5_secret}'
        ).format(
            settings.EPAY_MERCHANT_NUMBER,
            description,
            str(amount),
            str(order_id),
            accept_url,
            settings.EPAY_MD5_SECRET,
        )
        epay_hash = hashlib.md5(hashstring).hexdigest()

        context = super(EpayView, self).get_context_data(**kwargs)
        context['merchant_number'] = settings.EPAY_MERCHANT_NUMBER
        context['description'] = description
        context['order_id'] = order_id
        context['accept_url'] = accept_url
        context['amount'] = amount
        context['epay_hash'] = epay_hash
        return context


class EpayCallbackView(View):

    def get(self, request, **kwargs):

        callback = EpayCallback.objects.create(
            payload=request.GET
        )

        if 'orderid' in request.GET:
            ticket = Ticket.objects.get(pk=request.GET.get('order_id'))
            query = dict(
                map(
                    lambda x: tuple(x.split('=')),
                    request.META['QUERY_STRING'].split('&')
                )
            )

            hashstring = (
                '{merchantnumber}{description}11{amount}DKK'
                '{order_id}{accept_url}{md5_secret}'
            ).format(
                query.get('merchantnumber'),
                query.get('description'),
                query.get('amount'),
                query.get('order_id'),
                query.get('accept_url'),
                settings.EPAY_MD5_SECRET,
            )
            epay_hash = hashlib.md5(hashstring).hexdigest()

            if not epay_hash == request.GET['hash']:
                return HttpResponse(status=400)

            EpayPayment.objects.create(
                ticket=ticket,
                callback=callback,
                txnid=request.GET['txnid'],
            )
        else:
            return HttpResponse(status=400)

        return HttpResponse('OK')
