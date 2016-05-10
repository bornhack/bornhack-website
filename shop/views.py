import hashlib

from django.http import HttpResponseRedirect, Http404
from django.views.generic import CreateView, TemplateView, DetailView, View
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse

from .models import Order, Product, EpayCallback, EpayPayment


class ShopIndexView(TemplateView):
    template_name = "shop/index.html"

    def get_context_data(self, **kwargs):
        context = super(ShopIndexView, self).get_context_data(**kwargs)
        context['tickets'] = Product.objects.filter(category__name='Tickets')
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'product/detail.html'
    context_object_name = 'product'


# class EpayView(TemplateView):
#     template_name = 'tickets/epay_form.html'
#
#     def get_context_data(self, **kwargs):
#         ticket = Ticket.objects.get(pk=kwargs.get('ticket_id'))
#         accept_url = ticket.get_absolute_url()
#         amount = ticket.ticket_type.price * 100
#         order_id = str(ticket.pk)
#         description = str(ticket.user.pk)
#
#         hashstring = (
#             '{merchant_number}{description}11{amount}DKK'
#             '{order_id}{accept_url}{md5_secret}'
#         ).format(
#             merchant_number=settings.EPAY_MERCHANT_NUMBER,
#             description=description,
#             amount=str(amount),
#             order_id=str(order_id),
#             accept_url=accept_url,
#             md5_secret=settings.EPAY_MD5_SECRET,
#         )
#         epay_hash = hashlib.md5(hashstring).hexdigest()
#
#         context = super(EpayView, self).get_context_data(**kwargs)
#         context['merchant_number'] = settings.EPAY_MERCHANT_NUMBER
#         context['description'] = description
#         context['order_id'] = order_id
#         context['accept_url'] = accept_url
#         context['amount'] = amount
#         context['epay_hash'] = epay_hash
#         return context
#
#
# class EpayCallbackView(View):
#
#     def get(self, request, **kwargs):
#
#         callback = EpayCallback.objects.create(
#             payload=request.GET
#         )
#
#         if 'orderid' in request.GET:
#             ticket = Ticket.objects.get(pk=request.GET.get('order_id'))
#             query = dict(
#                 map(
#                     lambda x: tuple(x.split('=')),
#                     request.META['QUERY_STRING'].split('&')
#                 )
#             )
#
#             hashstring = (
#                 '{merchant_number}{description}11{amount}DKK'
#                 '{order_id}{accept_url}{md5_secret}'
#             ).format(
#                 merchant_number=query.get('merchantnumber'),
#                 description=query.get('description'),
#                 amount=query.get('amount'),
#                 order_id=query.get('orderid'),
#                 accept_url=query.get('accepturl'),
#                 md5_secret=settings.EPAY_MD5_SECRET,
#             )
#             epay_hash = hashlib.md5(hashstring).hexdigest()
#
#             if not epay_hash == request.GET['hash']:
#                 return HttpResponse(status=400)
#
#             EpayPayment.objects.create(
#                 ticket=ticket,
#                 callback=callback,
#                 txnid=request.GET['txnid'],
#             )
#         else:
#             return HttpResponse(status=400)
#
#         return HttpResponse('OK')
