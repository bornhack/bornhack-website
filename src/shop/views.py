from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.db.models import Count, F
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseBadRequest,
    Http404
)
from django.shortcuts import get_object_or_404
from django.views.generic import (
    View,
    ListView,
    DetailView,
    FormView,
)
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from shop.models import (
    Order,
    Product,
    OrderProductRelation,
    ProductCategory,
    EpayCallback,
    EpayPayment,
    CreditNote,
)
from .forms import AddToOrderForm
from .epay import calculate_epay_hash, validate_epay_callback
from collections import OrderedDict
from vendor.coinify.coinify_callback import CoinifyCallback
from .coinify import (
    create_coinify_invoice,
    save_coinify_callback,
    process_coinify_invoice_json
)
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


# Mixins
class EnsureCreditNoteHasPDFMixin(SingleObjectMixin):
    model = CreditNote

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().pdf:
            messages.error(request, "This creditnote has no PDF yet!")
            return HttpResponseRedirect(reverse_lazy('shop:creditnote_list'))

        return super(EnsureCreditNoteHasPDFMixin, self).dispatch(
            request, *args, **kwargs
        )


class EnsureUserOwnsCreditNoteMixin(SingleObjectMixin):
    model = CreditNote

    def dispatch(self, request, *args, **kwargs):
        # If the user does not own this creditnote OR is not staff
        if not request.user.is_staff:
            if self.get_object().user != request.user:
                raise Http404("CreditNote not found")

        return super(EnsureUserOwnsCreditNoteMixin, self).dispatch(
            request, *args, **kwargs
        )


class EnsureUserOwnsOrderMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        # If the user does not own this order OR is not staff
        if not request.user.is_staff:
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
            return HttpResponseRedirect(
                reverse_lazy('shop:order_detail', kwargs={'pk': self.get_object().pk})
            )

        return super(EnsureUnpaidOrderMixin, self).dispatch(
            request, *args, **kwargs
        )


class EnsurePaidOrderMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().paid:
            messages.error(request, "This order is not paid for!")
            return HttpResponseRedirect(
                reverse_lazy('shop:order_detail', kwargs={'pk': self.get_object().pk})
            )

        return super(EnsurePaidOrderMixin, self).dispatch(
            request, *args, **kwargs
        )


class EnsureClosedOrderMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().open is not None:
            messages.error(request, 'This order is still open!')
            return HttpResponseRedirect(
                reverse_lazy('shop:order_detail', kwargs={'pk': self.get_object().pk})
            )

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


class EnsureOrderIsNotCancelledMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().cancelled:
            messages.error(
                request,
                'Order #{} is cancelled!'.format(self.get_object().id)
            )
            return HttpResponseRedirect(reverse_lazy('shop:index'))

        return super(EnsureOrderIsNotCancelledMixin, self).dispatch(
            request, *args, **kwargs
        )


class EnsureOrderHasInvoicePDFMixin(SingleObjectMixin):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().invoice.pdf:
            messages.error(request, "This order has no invoice yet!")
            return HttpResponseRedirect(
                reverse_lazy('shop:order_detail', kwargs={'pk': self.get_object().pk})
            )

        return super(EnsureOrderHasInvoicePDFMixin, self).dispatch(
            request, *args, **kwargs
        )


# Shop views
class ShopIndexView(ListView):
    model = Product
    template_name = "shop_index.html"
    context_object_name = 'products'

    def get_queryset(self):
        queryset = super(ShopIndexView, self).get_queryset()
        return queryset.available().order_by('category__name', 'price', 'name')

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
            context['current_category'] = categoryobj
        context['categories'] = ProductCategory.objects.annotate(
            num_products=Count('products')
        ).filter(
            num_products__gt=0,
            public=True,
            products__available_in__contains=timezone.now()
        )
        return context


class ProductDetailView(FormView, DetailView):
    model = Product
    template_name = 'product_detail.html'
    form_class = AddToOrderForm
    context_object_name = 'product'

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().category.public:
            # this product is not publicly available
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
        return Order.objects.get(
            user=self.request.user, open__isnull=False
        ).get_absolute_url()


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "order_list.html"
    context_object_name = 'orders'

    def get_queryset(self):
        queryset = super(OrderListView, self).get_queryset()
        return queryset.filter(user=self.request.user).not_cancelled()


class OrderDetailView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureOrderHasProductsMixin, EnsureOrderIsNotCancelledMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        payment_method = request.POST.get('payment_method')

        if payment_method in order.PAYMENT_METHODS:
            if not request.POST.get('accept_terms'):
                messages.error(request, "You need to accept the general terms and conditions before you can continue!")
                return HttpResponseRedirect(
                    reverse_lazy('shop:order_detail', kwargs={'pk': order.pk})
                )

            # Set payment method and mark the order as closed
            order.payment_method = payment_method
            order.open = None
            order.customer_comment = request.POST.get('customer_comment') or ''
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
                ),
                Order.CASH: reverse_lazy(
                    'shop:cash',
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
            order.customer_comment = request.POST.get('customer_comment') or ''
            order.save()

        product_remove = request.POST.get('remove_product')
        if product_remove:
            order.orderproductrelation_set.filter(pk=product_remove).delete()
            if not order.products.count() > 0:
                order.mark_as_cancelled()
                messages.info(request, 'Order cancelled!')
                return HttpResponseRedirect(reverse_lazy('shop:index'))

        if 'cancel_order' in request.POST:
            order.mark_as_cancelled()
            messages.info(request, 'Order cancelled!')
            return HttpResponseRedirect(reverse_lazy('shop:index'))

        return super(OrderDetailView, self).get(request, *args, **kwargs)


class DownloadInvoiceView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsurePaidOrderMixin, EnsureOrderHasInvoicePDFMixin, SingleObjectMixin, View):
    model = Order

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % self.get_object().invoice.filename
        response.write(self.get_object().invoice.pdf.read())
        return response


class CreditNoteListView(LoginRequiredMixin, ListView):
    model = CreditNote
    template_name = "creditnote_list.html"
    context_object_name = 'creditnotes'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)


class DownloadCreditNoteView(LoginRequiredMixin, EnsureUserOwnsCreditNoteMixin, EnsureCreditNoteHasPDFMixin, SingleObjectMixin, View):
    model = CreditNote

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % self.get_object().filename
        response.write(self.get_object().pdf.read())
        return response


class OrderMarkAsPaidView(LoginRequiredMixin, SingleObjectMixin, View):

    model = Order

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'You do not have permissions to do that.')
            return HttpResponseRedirect(reverse_lazy('shop:index'))
        else:
            messages.success(request, 'The order has been marked as paid.')
            order = self.get_object()
            order.mark_as_paid()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Epay views
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

    def get(self, request, *args, **kwargs):
        callback = EpayCallback.objects.create(
            payload=request.GET
        )

        if 'orderid' in request.GET:
            query = OrderedDict(
                [tuple(x.split('=')) for x in request.META['QUERY_STRING'].split('&')]
            )
            order = get_object_or_404(Order, pk=query.get('orderid'))
            if order.pk != self.get_object().pk:
                logger.error("bad epay callback, orders do not match!")
                return HttpResponse(status=400)

            if validate_epay_callback(query):
                callback.md5valid=True
                callback.save()
            else:
                logger.error("bad epay callback!")
                return HttpResponse(status=400)

            if order.paid:
                # this order is already paid, perhaps we are seeing a double callback?
                return HttpResponse('OK')

            # epay callback is valid - has the order been paid in full?
            if int(query['amount']) == order.total * 100:
                # create an EpayPayment object linking the callback to the order
                EpayPayment.objects.create(
                    order=order,
                    callback=callback,
                    txnid=query.get('txnid'),
                )
                # and mark order as paid (this will create tickets)
                order.mark_as_paid(request)
            else:
                logger.error("valid epay callback with wrong amount detected")
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
            return HttpResponseRedirect(
                reverse('shop:epay_thanks', kwargs={'pk': self.get_object().pk})
            )

        return super(EpayThanksView, self).dispatch(
            request, *args, **kwargs
        )


# Bank Transfer view

class BankTransferView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureUnpaidOrderMixin, EnsureOrderHasProductsMixin, DetailView):
    model = Order
    template_name = 'bank_transfer.html'

    def get_context_data(self, **kwargs):
        context = super(BankTransferView, self).get_context_data(**kwargs)
        context['iban'] = settings.BANKACCOUNT_IBAN
        context['swiftbic'] = settings.BANKACCOUNT_SWIFTBIC
        context['orderid'] = self.get_object().pk
        context['regno'] = settings.BANKACCOUNT_REG
        context['accountno'] = settings.BANKACCOUNT_ACCOUNT
        context['total'] = self.get_object().total
        return context


# Cash payment view

class CashView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureUnpaidOrderMixin, EnsureOrderHasProductsMixin, DetailView):
    model = Order
    template_name = 'cash.html'


# Coinify views

class CoinifyRedirectView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureUnpaidOrderMixin, EnsureClosedOrderMixin, EnsureOrderHasProductsMixin, SingleObjectMixin, RedirectView):
    model = Order

    def dispatch(self, request, *args, **kwargs):
        order = self.get_object()

        # create a new coinify invoice if needed
        if not order.coinifyapiinvoice:
            coinifyinvoice = create_coinify_invoice(order, request)
            if not coinifyinvoice:
                messages.error(request, "There was a problem with the payment provider. Please try again later")
                return HttpResponseRedirect(
                    reverse_lazy('shop:order_detail', kwargs={'pk': self.get_object().pk})
                )

        return super(CoinifyRedirectView, self).dispatch(
            request, *args, **kwargs
        )

    def get_redirect_url(self, *args, **kwargs):
        return self.get_object().coinifyapiinvoice.invoicejson['payment_url']


class CoinifyCallbackView(SingleObjectMixin, View):
    model = Order

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CoinifyCallbackView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        # save callback and parse json payload
        callbackobject = save_coinify_callback(request, self.get_object())

        # do we have a json body?
        if not callbackobject.payload:
            # no, return an error
            logger.error("unable to parse JSON body in callback for order %s" % callbackobject.order.id)
            return HttpResponseBadRequest('unable to parse json')

        # initiate SDK
        sdk = CoinifyCallback(settings.COINIFY_IPN_SECRET.encode('utf-8'))

        # attemt to validate the callbackc
        if sdk.validate_callback(request.body, request.META['HTTP_X_COINIFY_CALLBACK_SIGNATURE']):
            # mark callback as valid in db
            callbackobject.valid = True
            callbackobject.save()
        else:
            logger.error("invalid coinify callback detected")
            return HttpResponseBadRequest('something is fucky')

        if callbackobject.payload['event'] == 'invoice_state_change' or callbackobject.payload['event'] == 'invoice_manual_resend':
            process_coinify_invoice_json(
                callbackobject.payload['data'],
                self.get_object()
            )
            return HttpResponse('OK')
        else:
            logger.error("unsupported callback event %s" % callbackobject.payload['event'])
            return HttpResponseBadRequest('unsupported event')


class CoinifyThanksView(LoginRequiredMixin, EnsureUserOwnsOrderMixin, EnsureClosedOrderMixin, DetailView):
    model = Order
    template_name = 'coinify_thanks.html'

