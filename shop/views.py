import hashlib

from django.http import HttpResponseRedirect, Http404
from django.views.generic import CreateView, TemplateView, DetailView, View, FormView
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


class CheckoutView(LoginRequiredMixin, DetailView):
    """
    Shows a summary of all products contained in an order, 
    total price, VAT, and a button to go to the payment
    """
    model = Order
    template_name = 'shop/order_detail.html'
    context_object_name = 'order'


class PaymentView(LoginRequiredMixin, FormView):
    """
    One final chance to change payment method (in case another method failed),
    and a submit button to intiate payment with selected metod
    """
    template_name = 'shop/payment.html'
    form_class = PaymentMethodForm

    def get(self, request, *args, **kwargs):
        if self.instance.user != self.request.user:
            raise Http404("Order not found")

        if self.instance.paid:
            messages.error('This order is already paid for!')
            return HttpResponseRedirect('shop:order_detail')

        if not self.instance.products:
            messages.error('This order contains no products!')
            return HttpResponseRedirect('shop:order_detail')

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        order = Order.objects.get(pk=kwargs.get('order_id'))
        context = super(CheckoutView, self).get_context_data(**kwargs)
        context['order'] = order
        return context


class CoinifyView(TemplateView):
    template_name = 'shop/coinify_form.html'
    
    def get_context_data(self, **kwargs):
        order = Order.objects.get(pk=kwargs.get('order_id'))
        context = super(CoinifyView, self).get_context_data(**kwargs)
        context['order'] = order
        
        coinifyapi = CoinifyAPI(settings.COINIFY_API_KEY, settings.COINIFY_API_SECRET)

        response = coinifyapi.invoice_create(
            amount,
            currency,
            plugin_name='BornHack 2016 webshop',
            plugin_version='1.0',
            description='BornHack 2016 order id #%s' % order.id,
            callback_url=reverse('shop:coinfy_callback', kwargs={'orderid': order.id}),
            return_url=reverse('shop:order_paid', kwargs={'orderid': order.id}),
        )

        if not response['success']:
            api_error = response['error']
            print "API error: %s (%s)" % (api_error['message'], api_error['code'] )

        invoice = response['data']
        ### change this to pass only needed data when we get that far
        context['invoice'] = invoice
        return context


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
