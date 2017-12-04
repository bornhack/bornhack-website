from django.views.generic import TemplateView, ListView
from django.shortcuts import redirect
from django.views import View
from django.conf import settings
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden
from shop.models import OrderProductRelation
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class StaffMemberRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)


class BackofficeIndexView(StaffMemberRequiredMixin, TemplateView):
    template_name = "backoffice_index.html"


class InfodeskView(StaffMemberRequiredMixin, ListView):
    template_name = "infodesk.html"
    queryset = OrderProductRelation.objects.filter(handed_out=False, order__paid=True, order__refunded=False, order__cancelled=False).order_by('order')

