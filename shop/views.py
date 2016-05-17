from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.db.models import Count, F
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.generic import (
    View,
    TemplateView,
    ListView,
    DetailView,
    FormView,
)
from django.views.generic.detail import SingleObjectMixin

from camps.models import Camp
from shop.models import (
    Order,
    Product,
    OrderProductRelation,
    ProductCategory,
    EpayCallback,
)
from .forms import AddToOrderForm
from .utils import calculate_epay_hash


class EnsureUserOwnsOrderMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().user != request.user:
            raise Http404("Order not found")

        return super(EnsureUserOwnsOrderMixin, self).dispatch(
            request, *args, **kwargs
        )


class ShopIndexView(ListView):
    model = Product
    template_name = "shop_index.html"
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super(ShopIndexView, self).get_context_data(**kwargs)

        if 'category' in self.request.GET:
            category = self.request.GET.get('category')
            context['products'] = context['products'].filter(
                category__slug=category
            )
            context['current_category'] = category
        context['categories'] = ProductCategory.objects.annotate(
            num_products=Count('products')
        ).filter(
            num_products__gt=0
        )
        return context


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "order_list.html"

    def get_context_data(self, **kwargs):
        context = super(OrderListView, self).get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(user=self.request.user)
        return context


class OrderDetailView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'

    def get(self, request, *args, **kwargs):
        order = self.get_object()

        if not order.products.count() > 0:
            return HttpResponseRedirect(reverse_lazy('shop:index'))

        return super(OrderDetailView, self).get(request, *args, **kwargs)

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


class ProductDetailView(LoginRequiredMixin, FormView, DetailView):
    model = Product
    template_name = 'product_detail.html'
    form_class = AddToOrderForm
    context_object_name = 'product'

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


class CoinifyRedirectView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, DetailView):
    model = Order
    template_name = 'coinify_redirect.html'

    def get(self, request, *args, **kwargs):
        # validate a few things
        order = self.get_object()

        if order.open is not None:
            messages.error(request, 'This order is still open!')
            return HttpResponseRedirect('shop:order_detail')

        if order.paid:
            messages.error(request, 'This order is already paid for!')
            return HttpResponseRedirect('shop:order_detail')

        if not order.products.count() > 0:
            messages.error(request, 'This order contains no products!')
            return HttpResponseRedirect('shop:order_detail')

        return super(CoinifyRedirectView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        order = self.get_object()
        context = super(CoinifyRedirectView, self).get_context_data(**kwargs)
        context['order'] = order

        # Initiate coinify API and create invoice
        coinifyapi = CoinifyAPI(
            settings.COINIFY_API_KEY,
            settings.COINIFY_API_SECRET
        )
        response = coinifyapi.invoice_create(
            amount,
            currency,
            plugin_name='BornHack 2016 webshop',
            plugin_version='1.0',
            description='BornHack 2016 order id #%s' % order.id,
            callback_url=reverse_lazy(
                'shop:coinfy_callback',
                kwargs={'orderid': order.id}
            ),
            return_url=reverse_lazy(
                'shop:order_paid',
                kwargs={'orderid': order.id}
            ),
        )

        if not response['success']:
            api_error = response['error']
            print "API error: %s (%s)" % (
                api_error['message'],
                api_error['code']
            )

        invoice = response['data']
        # change this to pass only needed data when we get that far
        context['invoice'] = invoice
        return context


class EpayFormView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, DetailView):
    model = Order
    template_name = 'epay_form.html'

    def get_context_data(self, **kwargs):
        order = self.get_object()
        accept_url = order.get_epay_accept_url(request)
        cancel_url = order.get_epay_cancel_url(request)
        amount = order.total * 100

        epay_hash = calculate_epay_hash(order, request)

        context = super(EpayFormView, self).get_context_data(**kwargs)
        context['merchant_number'] = settings.EPAY_MERCHANT_NUMBER
        context['description'] = order.description
        context['amount'] = amount
        context['order_id'] = order.pk
        context['accept_url'] = accept_url
        context['cancel_url'] = cancel_url
        context['epay_hash'] = epay_hash
        return context


class EpayCallbackView(View):
    def get(self, request, **kwargs):
        callback = EpayCallback.objects.create(
            payload=request.GET
        )

        if 'orderid' in request.GET:
            query = dict(
                map(
                    lambda x: tuple(x.split('=')),
                    request.META['QUERY_STRING'].split('&')
                )
            )
            order = get_object_or_404(Order, pk=query.get('orderid'))

            epay_hash = calculate_epay_hash(order, request)
            if not epay_hash == query.get('hash'):
                return HttpResponse(status=400)

            EpayPayment.objects.create(
                order=order,
                callback=callback,
                txnid=query.get('txnid'),
            )
        else:
            return HttpResponse(status=400)

        return HttpResponse('OK')


class EpayThanksView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, DetailView):
    model = Order
    template_name = 'epay_thanks.html'

    def dispatch(self, request, *args, **kwargs):
        if order.open:
            ### this order is open, what is the user doing here?
            return HttpResponseRedirect(reverse_lazy('shop:order_detail', kwargs={'pk': order.pk}))

        return super(EpayThanksView, self).dispatch(
            request, *args, **kwargs
        )


class BankTransferView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, DetailView):
    model = Order
    template_name = 'bank_transfer.html'

