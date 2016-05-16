from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.db.models import Count, F
from django.http import HttpResponseRedirect, Http404
from django.views.generic import (
    View,
    TemplateView,
    ListView,
    DetailView,
    FormView,
)
from camps.models import Camp
from shop.models import (
    Order,
    Product,
    OrderProductRelation,
    ProductCategory,
)
from .forms import AddToOrderForm


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


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'

    def get(self, request, *args, **kwargs):
        order = self.get_object()

        if order.user != request.user:
            raise Http404("Order not found")

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
        return reverse_lazy(
            'shop:product_detail',
            kwargs={'slug': self.get_object().slug}
        )


class CoinifyRedirectView(TemplateView):
    template_name = 'coinify_redirect.html'

    def get(self, request, *args, **kwargs):
        # validate a few things
        self.order = Order.objects.get(pk=kwargs.get('order_id'))
        if self.order.user != request.user:
            raise Http404("Order not found")

        if self.order.open is None:
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
            callback_url=reverse(
                'shop:coinfy_callback',
                kwargs={'orderid': order.id}
            ),
            return_url=reverse(
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


class EpayFormView(TemplateView):
    template_name = 'epay_form.html'

    def get_context_data(self, **kwargs):
        order = Order.objects.get(pk=kwargs.get('pk'))
        accept_url = order.get_absolute_url()
        amount = order.total
        order_id = str(order.pk)
        description = "BornHack 2016 order #%s" % order.pk

        hashstring = (
            '{merchant_number}{description}11{amount}DKK'
            '{order_id}{accept_url}{md5_secret}'
        ).format(
            merchant_number=settings.EPAY_MERCHANT_NUMBER,
            description=description,
            amount=str(amount),
            order_id=order_id,
            accept_url=accept_url,
            md5_secret=settings.EPAY_MD5_SECRET,
        )
        epay_hash = hashlib.md5(hashstring).hexdigest()

        context = super(EpayFormView, self).get_context_data(**kwargs)
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
            order = Order.objects.get(pk=request.GET.get('order_id'))
            query = dict(
                map(
                    lambda x: tuple(x.split('=')),
                    request.META['QUERY_STRING'].split('&')
                )
            )

            hashstring = (
                '{merchant_number}{description}11{amount}DKK'
                '{order_id}{accept_url}{md5_secret}'
            ).format(
                merchant_number=query.get('merchantnumber'),
                description=query.get('description'),
                amount=query.get('amount'),
                order_id=query.get('orderid'),
                accept_url=query.get('accepturl'),
                md5_secret=settings.EPAY_MD5_SECRET,
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


class BankTransferView(TemplateView):
    template_name = 'epay_form.html'

