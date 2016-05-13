import hashlib

from django.http import HttpResponseRedirect, Http404
from django.views.generic import CreateView, TemplateView, ListView, DetailView, View, FormView
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.contrib import messages

from .models import Order, Product, EpayCallback, EpayPayment, OrderProductRelation
from .forms import CheckoutForm, AddToOrderForm


class ShopIndexView(ListView):
    model = Product
    template_name = "shop_index.html"

    def get_context_data(self, **kwargs):
        context = super(ShopIndexView, self).get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(user=self.request.user)
        return context


class ProductDetailView(LoginRequiredMixin, FormView):
    model = Product
    template_name = 'product_detail.html'
    form_class = 'AddToOrderForm'
    context_object_name = 'product'

    def get(self, request, *args, **kwargs):
        self.product == Product.objects.get(id=kwargs.get('product_id'))

    def form_valid(self, form):
        ### do we have an open order?
        try:
            order = Order.objects.get(user=self.request.user, finalized=False)
        except Order.DoesNotExist:
            ### no open order - open a new one
            order = Order.objects.create(user=request.user)

        ### get product from kwargs
        if self.product in order.products.all():
            ### this product is already added to this order, increase count by one
            OrderProductRelation.objects.filter(product=self.product, order=order).update(quantity=F('quantity') + 1)
        else:
            order.products.add(self.product)

        ### done
        return super(ProductDetailView, self).form_valid(form)


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'order_detail.html'
    context_object_name = 'order'


class CheckoutView(LoginRequiredMixin, FormView):
    """
    Shows a summary of all products contained in an order, 
    total price, VAT info, and a button to finalize order and go to payment
    """
    model = Order
    template_name = 'checkout.html'
    form_class='CheckoutForm'
    context_object_name = 'order'

    def get(self, request, *args, **kwargs):
        if self.get_object().user != request.user:
            raise Http404("Order not found")

        if self.get_object().paid:
            messages.error(request, 'This order is already paid for!')
            return HttpResponseRedirect('shop:order_detail')

        if not self.get_object().products:
            messages.error(request, 'This order contains no products!')
            return HttpResponseRedirect('shop:order_detail')

        return self.render_to_response(self.get_context_data())

    def form_valid(self, form):
        ### mark order as finalized and redirect user to payment
        form.instance.finalized=True

        ### set payment_method based on submit button used
        if 'credit_card' in form.data:
            form.instance.payment_method=='credit_card'
        elif 'blockchain' in form.data:
            form.instance.payment_method=='blockchain'
        elif 'bank_transfer' in form.data:
            form.instance.payment_method=='bank_transfer'
        else:
            ### unknown submit button
            messages.error(request, 'Unknown submit button :(')
            return reverse('shop:checkout', kwargs={'orderid': self.get_object.id})

        return super(CheckoutView, self).form_valid(form)

    def get_success_url(self):
        if self.get_object.payment_method == 'credit_card':
            return reverse('shop:epay_form', kwargs={'orderid': self.get_object.id})
        elif self.get_object.payment_method == 'blockchain':
            return reverse('shop:coinify_pay', kwargs={'orderid': self.get_object.id})
        elif self.get_object.payment_method == 'bank_transfer':
            return reverse('shop:bank_transfer', kwargs={'orderid': self.get_object.id})
        else:
            ### unknown payment method
            messages.error(request, 'Unknown payment method :(')
            return reverse('shop:checkout', kwargs={'orderid': self.get_object.id})


class CoinifyRedirectView(TemplateView):
    template_name = 'coinify_redirect.html'
    
    def get(self, request, *args, **kwargs):
        ### validate a few things
        self.order = Order.objects.get(pk=kwargs.get('order_id'))
        if self.order.user != request.user:
            raise Http404("Order not found")

        if not self.order.finalized:
            messages.error(request, 'This order is still open!')
            return HttpResponseRedirect('shop:order_detail')

        if self.order.paid:
            messages.error(request, 'This order is already paid for!')
            return HttpResponseRedirect('shop:order_detail')

        if not self.get_object().products:
            messages.error(request, 'This order contains no products!')
            return HttpResponseRedirect('shop:order_detail')

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        order = Order.objects.get(pk=kwargs.get('order_id'))
        context = super(CoinifyRedirectView, self).get_context_data(**kwargs)
        context['order'] = order
        
        ### Initiate coinify API and create invoice
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
