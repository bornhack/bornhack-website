import logging

import requests
from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.views.generic import TemplateView

from camps.mixins import CampViewMixin
from facilities.models import FacilityFeedback
from teams.models import Team
from utils.mixins import AnyTeamMemberRequiredMixin
from utils.mixins import RaisePermissionRequiredMixin
from utils.models import OutgoingEmail

logger = logging.getLogger("bornhack.%s" % __name__)


class BackofficeIndexView(CampViewMixin, AnyTeamMemberRequiredMixin, TemplateView):
    """The Backoffice index view is available to anyone who is an approved member of any team for the current camp."""

    template_name = "index.html"

    def get_index_tabs(self, perms, context):
        tabs = {}
        if (
            "camps.orga_team_member" in perms
            or "camps.gis_team_member" in perms
            or context["facilityfeedback_teams"]
            or context["is_team_facilitator"]
        ):
            tabs["facilities"] = {
                "name": "Facilities",
                "count": context["feedback_count"].count(),
            }
        if "camps.info_team_member" in perms:
            tabs["info"] = {"name": "Info"}
        if "camps.content_team_member" in perms:
            tabs["content"] = {"name": "Content"}
        if "camps.orga_team_member" in perms:
            tabs["orga"] = {"name": "Orga", "count": context["held_email_count"]}
        if "camps.economy_team_member" in perms:
            tabs["economy"] = {"name": "Economy"}
        if "camps.orga_team_member" in perms or context["is_team_pos"]:
            tabs["pos"] = {"name": "Pos"}
        if "camps.game_team_member" in perms:
            tabs["game"] = {"name": "Game Team"}
        if "camps.gis_team_member" in perms or context["is_team_mapper"]:
            tabs["map"] = {"name": "Maps"}
        if "camps.orga_team_member" in perms or context["is_team_lead"]:
            tabs["permissions"] = {"name": "Permissions"}
        return tabs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # get user permissions
        perms = self.request.user.get_all_permissions()

        # get slugs for teams the user has member permission for
        team_slugs = [perm.split(".")[1].split("_")[0] for perm in perms if perm.endswith("_team_member")]
        # generate a list of teams with unhandled facility feedback
        context["facilityfeedback_teams"] = Team.objects.filter(
            slug__in=team_slugs,
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

        context["feedback_count"] = FacilityFeedback.objects.filter(
            facility__facility_type__responsible_team__camp=self.camp,
            facility__facility_type__responsible_team__slug__in=team_slugs,
            handled=False,
        )

        # include the number of unread emails
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

        # add bools for each of settings.BORNHACK_TEAM_PERMISSIONS
        for perm in settings.BORNHACK_TEAM_PERMISSIONS.keys():
            # loop over user permissions and set context
            for user_perm in perms:
                if user_perm.startswith("camps.") and user_perm.endswith(
                    f"_team_{perm}",
                ):
                    context[f"is_team_{perm}"] = True
                    break
            else:
                context[f"is_team_{perm}"] = False
        context["backoffice_tabs"] = self.get_index_tabs(perms, context)
        return context


class BackofficeProxyView(CampViewMixin, RaisePermissionRequiredMixin, TemplateView):
    """Show proxied stuff, only for simple HTML pages with no external content
    Define URLs in settings.BACKOFFICE_PROXY_URLS as a dict of slug: (description, url) pairs
    """

    permission_required = "camps.orga_team_member"
    template_name = "backoffice_proxy.html"

    def dispatch(self, request, *args, **kwargs):
        """Perform the request and return the response if we have a slug"""
        # list available stuff if we have no slug
        if "proxy_slug" not in kwargs:
            return super().dispatch(request, *args, **kwargs)

        # is the slug valid?
        if kwargs["proxy_slug"] not in settings.BACKOFFICE_PROXY_URLS.keys():
            raise Http404

        # perform the request
        description, url = settings.BACKOFFICE_PROXY_URLS[kwargs["proxy_slug"]]
        r = requests.get(url)

        # return the response, keeping the status code but no headers
        return HttpResponse(r.content, status=r.status_code)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["urls"] = settings.BACKOFFICE_PROXY_URLS
        return context
