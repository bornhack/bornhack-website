from django.views.generic import TemplateView, ListView
from django.http import HttpResponseForbidden
from shop.models import OrderProductRelation
from tickets.models import ShopTicket, SponsorTicket, DiscountTicket
from itertools import chain
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class StaffMemberRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class BackofficeIndexView(StaffMemberRequiredMixin, TemplateView):
    template_name = "backoffice_index.html"


class ProductHandoutView(StaffMemberRequiredMixin, ListView):
    template_name = "product_handout.html"
    queryset = OrderProductRelation.objects.filter(handed_out=False, order__paid=True, order__refunded=False, order__cancelled=False).order_by('order')


class BadgeHandoutView(StaffMemberRequiredMixin, ListView):
    template_name = "badge_handout.html"
    context_object_name = 'tickets'

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(badge_handed_out=False)
        sponsortickets = SponsorTicket.objects.filter(badge_handed_out=False)
        discounttickets = DiscountTicket.objects.filter(badge_handed_out=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class TicketCheckinView(StaffMemberRequiredMixin, ListView):
    template_name = "ticket_checkin.html"
    context_object_name = 'tickets'

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(checked_in=False)
        sponsortickets = SponsorTicket.objects.filter(checked_in=False)
        discounttickets = DiscountTicket.objects.filter(checked_in=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))

