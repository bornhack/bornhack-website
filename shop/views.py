from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Count, F
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import (
    View,
    TemplateView,
    ListView,
    DetailView,
    FormView,
)
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from camps.models import Camp
from shop.models import (
    Order,
    Product,
    OrderProductRelation,
    ProductCategory,
    EpayCallback,
    EpayPayment,
    CoinifyAPIInvoice,
    CoinifyAPICallback,
)
from .forms import AddToOrderForm
from .epay import calculate_epay_hash, validate_epay_callback
from collections import OrderedDict
from vendor.coinify_api import CoinifyAPI
from vendor.coinify_callback import CoinifyCallback


class EnsureUserOwnsOrderMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().user != request.user:
            raise Http404("Order not found")

        return super(EnsureUserOwnsOrderMixin, self).dispatch(
            request, *args, **kwargs
        )


class EnsureUnpaidOrderMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().paid:
            messages.error(request, "This order is already paid for!")
            return HttpResponseRedirect(reverse_lazy('shop:order_detail', kwargs={'pk': self.get_object().pk}))

        return super(EnsureUnpaidOrderMixin, self).dispatch(
            request, *args, **kwargs
        )


class EnsureClosedOrderMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().open is not None:
            messages.error(request, 'This order is still open!')
            return HttpResponseRedirect(reverse_lazy('shop:order_detail', kwargs={'pk': self.get_object().pk}))

        return super(EnsureClosedOrderMixin, self).dispatch(
            request, *args, **kwargs
        )


class EnsureOrderHasProductsMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().products.count() > 0:
            messages.error(request, 'This order has no products!')
            return HttpResponseRedirect(reverse_lazy('shop:index'))

        return super(EnsureOrderHasProductsMixin, self).dispatch(
            request, *args, **kwargs
        )

#################################################################################

class ShopIndexView(ListView):
    model = Product
    template_name = "shop_index.html"
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super(ShopIndexView, self).get_context_data(**kwargs)

        if 'category' in self.request.GET:
            category = self.request.GET.get('category')

            # is this a public category
            try:
                categoryobj = ProductCategory.objects.get(slug=category)
                if not categoryobj.public:
                    raise Http404("Category not found")
            except ProductCategory.DoesNotExist:
                raise Http404("Category not found")

            # filter products by the chosen category
            context['products'] = context['products'].filter(
                category__slug=category
            )
            context['current_category'] = category
        context['categories'] = ProductCategory.objects.annotate(
            num_products=Count('products')
        ).filter(
            num_products__gt=0,
            public=True,
        )
        return context


class ProductDetailView(LoginRequiredMixin, FormView, DetailView):
    model = Product
    template_name = 'product_detail.html'
    form_class = AddToOrderForm
    context_object_name = 'product'

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().category.public:
            ### this product is not publicly available
            raise Http404("Product not found")

        return super(ProductDetailView, self).dispatch(
            request, *args, **kwargs
        )

    def form_valid(self, form):
        product = self.get_object()
        quantity = form.cleaned_data.get('quantity')

        # do we have an open order?
        try:
            order = Order.objects.get(
                user=self.request.user,
                open__isnull=False
            )
        except Order.DoesNotExist:
            # no open order - open a new one
            order = Order.objects.create(
                user=self.request.user,
                camp=Camp.objects.current()
            )

        # get product from kwargs
        if product in order.products.all():
            # this product is already added to this order,
            # increase count by quantity
            OrderProductRelation.objects.filter(
                product=product,
                order=order
            ).update(quantity=F('quantity') + quantity)
        else:
            order.orderproductrelation_set.create(
                product=product,
                quantity=quantity,
            )

        messages.info(
            self.request,
            '{}x {} has been added to your order.'.format(
                quantity,
                product.name
            )
        )

        # done
        return super(ProductDetailView, self).form_valid(form)

    def get_success_url(self):
        return Order.objects.get(user=self.request.user, open__isnull=False).get_absolute_url()


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "order_list.html"

    def get_context_data(self, **kwargs):
        context = super(OrderListView, self).get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(user=self.request.user)
        return context


class OrderDetailView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureOrderHasProductsMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        payment_method = request.POST.get('payment_method')

        if payment_method in order.PAYMENT_METHODS:
            order.payment_method = payment_method

            # Mark the order as closed
            order.open = None
            order.save()

            reverses = {
                Order.CREDIT_CARD: reverse_lazy(
                    'shop:epay_form',
                    kwargs={'pk': order.id}
                ),
                Order.BLOCKCHAIN: reverse_lazy(
                    'shop:coinify_pay',
                    kwargs={'pk': order.id}
                ),
                Order.BANK_TRANSFER: reverse_lazy(
                    'shop:bank_transfer',
                    kwargs={'pk': order.id}
                )
            }

            return HttpResponseRedirect(reverses[payment_method])

        if 'update_order' in request.POST:
            for order_product in order.orderproductrelation_set.all():
                order_product_id = str(order_product.pk)
                if order_product_id in request.POST:
                    new_quantity = int(request.POST.get(order_product_id))
                    order_product.quantity = new_quantity
                    order_product.save()

        product_remove = request.POST.get('remove_product')
        if product_remove:
            order.orderproductrelation_set.filter(pk=product_remove).delete()
            if not order.products.count() > 0:
                return HttpResponseRedirect(reverse_lazy('shop:index'))

        return super(OrderDetailView, self).get(request, *args, **kwargs)

#################################################################################

class EpayFormView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureUnpaidOrderMixin, EnsureClosedOrderMixin, EnsureOrderHasProductsMixin, DetailView):
    model = Order
    template_name = 'epay_form.html'

    def get_context_data(self, **kwargs):
        order = self.get_object()
        context = super(EpayFormView, self).get_context_data(**kwargs)
        context['merchant_number'] = settings.EPAY_MERCHANT_NUMBER
        context['description'] = order.description
        context['amount'] = order.total * 100
        context['order_id'] = order.pk
        context['accept_url'] = order.get_epay_accept_url(self.request)
        context['cancel_url'] = order.get_cancel_url(self.request)
        context['callback_url'] = order.get_epay_callback_url(self.request)
        context['epay_hash'] = calculate_epay_hash(order, self.request)
        return context


class EpayCallbackView(SingleObjectMixin, View):
    model = Order

    def get(self, request, **kwargs):
        callback = EpayCallback.objects.create(
            payload=request.GET
        )

        if 'orderid' in request.GET:
            query = OrderedDict(
                map(
                    lambda x: tuple(x.split('=')),
                    request.META['QUERY_STRING'].split('&')
                )
            )
            order = get_object_or_404(Order, pk=query.get('orderid'))
            if order.pk != self.get_object().pk:
                print "bad epay callback, orders do not match!"
                return HttpResponse(status=400)

            if validate_epay_callback(query):
                callback.md5valid=True
                callback.save()
            else:
                print "bad epay callback!"
                return HttpResponse(status=400)
            
            if order.paid:
                ### this order is already paid, perhaps we are seeing a double callback?
                return HttpResponse('OK')

            ### epay callback is valid - has the order been paid in full?
            if int(query['amount']) == order.total * 100:
                ### create an EpayPayment object linking the callback to the order
                EpayPayment.objects.create(
                    order=order,
                    callback=callback,
                    txnid=query.get('txnid'),
                )
                ### and mark order as paid
                order.paid=True
                order.save()
            else:
                print "valid epay callback with wrong amount detected"
        else:
            return HttpResponse(status=400)

        return HttpResponse('OK')


class EpayThanksView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureClosedOrderMixin, DetailView):
    model = Order
    template_name = 'epay_thanks.html'

    def dispatch(self, request, *args, **kwargs):
        if request.GET:
            # epay redirects the user back to our accepturl with a long
            # and ugly querystring, redirect user to the clean url
            return HttpResponseRedirect(reverse('shop:epay_thanks', kwargs={'pk': self.get_object().pk}))

        return super(EpayThanksView, self).dispatch(
            request, *args, **kwargs
        )

#################################################################################

class BankTransferView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureUnpaidOrderMixin, EnsureOrderHasProductsMixin, DetailView):
    model = Order
    template_name = 'bank_transfer.html'

#################################################################################

class CoinifyRedirectView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureUnpaidOrderMixin, EnsureClosedOrderMixin, EnsureOrderHasProductsMixin, SingleObjectMixin, RedirectView):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()

        if not hasattr(order, 'coinifyapiinvoice'):
            # Initiate coinify API
            coinifyapi = CoinifyAPI(
                settings.COINIFY_API_KEY,
                settings.COINIFY_API_SECRET
            )
            
            # create coinify API
            response = coinifyapi.invoice_create(
                order.total,
                'DKK',
                plugin_name='BornHack 2016 webshop',
                plugin_version='1.0',
                description='BornHack 2016 order id #%s' % order.id,
                callback_url=order.get_coinify_callback_url(request),
                return_url=order.get_coinify_thanks_url(request),
                cancel_url=order.get_cancel_url(request),
            )

            # Parse response
            if not response['success']:
                api_error = response['error']
                print "API error: %s (%s)" % (
                    api_error['message'],
                    api_error['code']
                )
                messages.error(request, "There was a problem with the payment provider. Please try again later")
                return HttpResponseRedirect(reverse_lazy('shop:order_detail', kwargs={'pk': self.get_object().pk}))
            else:
                # save this coinify invoice
                CoinifyAPIInvoice.objects.create(
                    invoicejson = response['data'],
                    order = order,
                )

        return super(CoinifyRedirectView, self).dispatch(
            request, *args, **kwargs
        )

    def get_redirect_url(self, *args, **kwargs):
        return self.get_object().coinifyapiinvoice.invoicejson['payment_url']


class CoinifyCallbackView(SingleObjectMixin, View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CoinifyCallbackView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Get the signature from the HTTP headers
        signature = request.META['HTTP_X_COINIFY_CALLBACK_SIGNATURE']
        sdk = CoinifyCallback(settings.COINIFY_API_SECRET)

        # make a dict with all HTTP_ headers
        headerdict = {}
        for key, value in request.META.iteritems():
            if key[:5] == 'HTTP_':
                headerdict[key[5:]] = value

        # save callback to db
        callbackobject = CoinifyAPICallback.objects.create(
            headers=json.dumps(headerdict),
            payload=request.body,
            order=self.get_object()
        )
        if sdk.validate_callback(request.body, signature):
            # mark callback as valid in db
            callbackobject.valid=True
            callbackobject.save()

            # parse json
            callbackjson = json.loads(request.body)
            if callbackjson['event'] == 'invoice_state_change' or callbackjson['event'] == 'invoice_manual_resend':
                # get invoice from db
                try:
                    invoice = CoinifyAPIInvoice.objects.get(id=callbackjson['data']['id'])
                except CoinifyAPIInvoice.DoesNotExist:
                    return HttpResponseBadRequest('bad invoice id')

                # save new invoice payload
                invoice.payload = callbackjson['data']
                invoice.save()
                
                # so, is the invoice paid now?
                if callbackjson['data']['state'] == 'complete':
                    invoice.order.mark_as_paid()
            else:
                HttpResponseBadRequest('unsupported event')
        else:
            print "invalid callback detected"
            HttpResponseBadRequest('something is fucky')


class CoinifyThanksView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureClosedOrderMixin, DetailView):
    model = Order
    template_name = 'coinify_thanks.html'

