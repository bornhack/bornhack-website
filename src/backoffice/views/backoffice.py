from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

import requests
from camps.mixins import CampViewMixin
from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.views.generic import TemplateView
from facilities.models import FacilityFeedback
from teams.models import Team
from utils.models import OutgoingEmail

from ..mixins import RaisePermissionRequiredMixin

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger(f"bornhack.{__name__}")


class BackofficeIndexView(CampViewMixin, RaisePermissionRequiredMixin, TemplateView):
    """The Backoffice index view only requires camps.backoffice_permission so we use RaisePermissionRequiredMixin directly"""

    permission_required = "camps.backoffice_permission"
    template_name = "index.html"

    def get_context_data(self, *args: list[Any], **kwargs: dict[str, Any]):
        context = super().get_context_data(*args, **kwargs)
        context["facilityfeedback_teams"] = Team.objects.filter(
            id__in=set(
                FacilityFeedback.objects.filter(
                    facility__facility_type__responsible_team__camp=self.camp,
                    handled=False,
                ).values_list(
                    "facility__facility_type__responsible_team__id",
                    flat=True,
                ),
            ),
        )
        context["held_email_count"] = (
            OutgoingEmail.objects.filter(
                hold=True,
                responsible_team__isnull=True,
            ).count()
            + OutgoingEmail.objects.filter(
                hold=True,
                responsible_team__camp=self.camp,
            ).count()
        )

        context["camp"] = self.camp

        return context


class BackofficeProxyView(CampViewMixin, RaisePermissionRequiredMixin, TemplateView):
    """Show proxied stuff, only for simple HTML pages with no external content
    Define URLs in settings.BACKOFFICE_PROXY_URLS as a dict of slug: (description, url) pairs
    """

    permission_required = "camps.backoffice_permission"
    template_name = "backoffice_proxy.html"

    def dispatch(self, request: HttpRequest, *args: list[Any], **kwargs: dict[str, Any]):
        """Perform the request and return the response if we have a slug"""
        # list available stuff if we have no slug
        if "proxy_slug" not in kwargs:
            return super().dispatch(request, *args, **kwargs)

        # is the slug valid?
        if kwargs["proxy_slug"] not in settings.BACKOFFICE_PROXY_URLS:
            raise Http404

        # perform the request
        description, url = settings.BACKOFFICE_PROXY_URLS[kwargs["proxy_slug"]]
        r = requests.get(url)

        # return the response, keeping the status code but no headers
        return HttpResponse(r.content, status=r.status_code)

    def get_context_data(self, *args: list[Any], **kwargs: dict[str, Any]):
        context = super().get_context_data(*args, **kwargs)
        context["urls"] = settings.BACKOFFICE_PROXY_URLS
        return context
