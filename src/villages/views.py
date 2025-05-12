"""Village related views."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http import HttpResponseRedirect
from django.templatetags.static import static
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.detail import SingleObjectMixin
from jsonview.views import JsonView
from leaflet.forms.widgets import LeafletWidget

from camps.mixins import CampViewMixin
from utils.widgets import MarkdownWidget

from .email import add_village_approve_email
from .models import Village

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.forms import ModelForm
    from django.http import HttpRequest
    from django.http import HttpResponse

class VillageListView(CampViewMixin, ListView):
    """List villages."""
    model = Village
    template_name = "village_list.html"
    context_object_name = "villages"

    def get_context_data(self, **kwargs) -> dict[str, dict[str,str]]:
        """Add village map data to context."""
        context = super().get_context_data(**kwargs)
        context["mapData"] = {"grid": static("json/grid.geojson")}
        return context

    def get_queryset(self) -> QuerySet[Village]:
        """Only show approved and not deleted villages."""
        return super().get_queryset().filter(deleted=False, approved=True)


class VillageMapView(CampViewMixin, ListView):
    """The village map view."""
    model = Village
    template_name = "village_map.html"
    context_object_name = "villages"

    def get_context_data(self, **kwargs) -> dict[str, str | bool]:
        """Add village map data to context."""
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "grid": static("json/grid.geojson"),
            "url": reverse("villages_geojson", kwargs={"camp_slug": self.camp.slug}),
            "loggedIn": self.request.user.is_authenticated,
        }
        return context

    def get_queryset(self) -> QuerySet[Village]:
        """Only show approved and not deleted villages."""
        return super().get_queryset().filter(deleted=False, approved=True)



class VillageListGeoJSONView(CampViewMixin, JsonView):
    """GeoJSON view for the village list."""
    def get_context_data(self, **kwargs) -> dict[str, str | dict[str, str]]:
        """Add type and features to context."""
        return {"type": "FeatureCollection", "features": self.dump_features()}

    def dump_features(self) -> list[object]:
        """Dump villages as geojson."""
        output = []
        for village in Village.objects.filter(
            camp=self.camp,
            deleted=False,
            approved=True,
        ):
            if village.location is None:
                continue
            entry = {
                "type": "Feature",
                "id": village.pk,
                "geometry": {
                    "type": "Point",
                    "coordinates": [village.location.x, village.location.y],
                },
                "properties": {
                    "name": village.name,
                    "marker": "greenIcon",
                    "icon": "campground",
                    "description": village.description,
                    "uuid": None,
                    "type": "village",
                    "detail_url": reverse(
                        "village_detail",
                        kwargs={"camp_slug": village.camp.slug, "slug": village.slug},
                    ),
                },
            }
            output.append(entry)
        return list(output)


class VillageDetailView(CampViewMixin, DetailView):
    """DetailView for villages."""
    model = Village
    template_name = "village_detail.html"
    context_object_name = "village"

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """If the user is not contact for this village, is not staff, and village not approved return 404."""
        if not request.user.is_staff and self.get_object().contact != request.user and not self.get_object().approved:
            raise Http404("NotFound")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs) -> dict[str, str | bool]:
        """Add village map data to context."""
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "grid": static("json/grid.geojson"),
            "x": context["village"].location.x,
            "y": context["village"].location.y,
            "loggedIn": self.request.user.is_authenticated,
        }
        return context

    def get_queryset(self) -> QuerySet[Village]:
        """Do not show deleted villages."""
        return super().get_queryset().filter(deleted=False)


class VillageCreateView(
    CampViewMixin,
    LoginRequiredMixin,
    CreateView,
):
    """Village CreateView."""
    model = Village
    template_name = "village_form.html"
    fields = ("name", "description", "private", "location")

    def get_context_data(self, **kwargs) -> dict[str, dict[str,str]]:
        """Add village map data to context."""
        context = super().get_context_data(**kwargs)
        context["mapData"] = {"grid": static("json/grid.geojson")}
        return context

    def get_form(self, *args, **kwargs) -> ModelForm[Village]:
        """Fill the form with nice widgets."""
        form = super().get_form(*args, **kwargs)
        form.fields["description"].widget = MarkdownWidget()
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "map_height": "500px",
                "class": "form-control",
                "geom_type": "Point",
            },
        )
        return form

    def form_valid(self, form: ModelForm[Village]) -> HttpResponseRedirect:
        """Set contact and camp, send email, return to village list."""
        village = form.save(commit=False)
        village.contact = self.request.user
        village.camp = self.camp
        if not village.name:
            village.name = "noname"
        village.save()
        messages.success(
            self.request,
            "Your request to create a village has been registered - it will be published after CoC compliance review",
        )
        add_village_approve_email(village)
        return HttpResponseRedirect(village.get_absolute_url())

    def get_success_url(self) -> str:
        """Return to village list after create."""
        return reverse_lazy("village_list", kwargs={"camp_slug": self.object.camp.slug})


class EnsureUserOwnsVillageMixin(SingleObjectMixin):
    """Mixin to ensure user is contact for the village, or staff."""
    model = Village

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """If the user is not contact for this village OR is not staff raise 404."""
        if not request.user.is_staff and self.get_object().contact != request.user:
            raise Http404("NotFound")
        return super().dispatch(request, *args, **kwargs)


class VillageUpdateView(
    CampViewMixin,
    EnsureUserOwnsVillageMixin,
    LoginRequiredMixin,
    UpdateView,
):
    """Village update view."""
    model = Village
    template_name = "village_form.html"
    fields = ("name", "description", "private", "location")

    def get_context_data(self, **kwargs) -> dict[str, dict[str,str]]:
        """Add village map data to context."""
        context = super().get_context_data(**kwargs)
        context["mapData"] = {"grid": static("json/grid.geojson")}
        return context

    def get_form(self, *args, **kwargs) -> ModelForm[Village]:
        """Add leaflet to the form."""
        form = super().get_form(*args, **kwargs)
        form.fields["location"].widget = LeafletWidget(
            attrs={
                "display_raw": "true",
                "map_height": "500px",
                "class": "form-control",
                "geom_type": "Point",
            },
        )
        return form

    def form_valid(self, form: ModelForm[Village]) -> HttpResponse:
        """Set village as not approved before saving, send email."""
        village = form.save(commit=False)
        village.approved = False
        if not village.name:
            village.name = "noname"
        messages.success(
            self.request,
            "Your village will be republished after the changes have been reviewed for CoC compliance.",
        )
        add_village_approve_email(village)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return to village detail page after editing."""
        return self.get_object().get_absolute_url()

    def get_queryset(self) -> QuerySet[Village]:
        """Do not allow editing deleted villages."""
        return super().get_queryset().filter(deleted=False)


class VillageDeleteView(
    CampViewMixin,
    EnsureUserOwnsVillageMixin,
    LoginRequiredMixin,
    DeleteView,
):
    """Village delete view."""
    model = Village
    template_name = "village_confirm_delete.html"
    context_object_name = "village"

    def get_success_url(self) -> str:
        """Return to village list after deleting."""
        return reverse_lazy("village_list", kwargs={"camp_slug": self.object.camp.slug})
