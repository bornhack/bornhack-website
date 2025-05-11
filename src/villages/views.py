from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.templatetags.static import static
from jsonview.views import JsonView
from leaflet.forms.widgets import LeafletWidget

from .email import add_village_approve_email
from .models import Village
from camps.mixins import CampViewMixin
from camps.models import Camp
from utils.widgets import MarkdownWidget


class VillageListView(CampViewMixin, ListView):
    model = Village
    template_name = "village_list.html"
    context_object_name = "villages"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {"grid": static("json/grid.geojson")}
        return context

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False, approved=True)


class VillageMapView(CampViewMixin, ListView):
    model = Village
    template_name = "village_map.html"
    context_object_name = "villages"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "grid": static("json/grid.geojson"),
            "url": reverse("villages_geojson", kwargs={"camp_slug": self.camp.slug}),
            "loggedIn": self.request.user.is_authenticated,
        }
        return context

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False, approved=True)


class UserOwnsVillageOrApprovedMixin(SingleObjectMixin):
    model = Village

    def dispatch(self, request, *args, **kwargs):
        # If the user is not contact for this village OR is not staff and village not approved
        if not request.user.is_staff:
            if (
                self.get_object().contact != request.user
                and not self.get_object().approved
            ):
                raise Http404("Village not found")

        return super().dispatch(request, *args, **kwargs)


class VillageListGeoJSONView(CampViewMixin, JsonView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["type"] = "FeatureCollection"
        context["features"] = self.dump_features()
        return context

    def dump_features(self) -> list[object]:
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


class VillageDetailView(CampViewMixin, UserOwnsVillageOrApprovedMixin, DetailView):
    model = Village
    template_name = "village_detail.html"
    context_object_name = "village"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {
            "grid": static("json/grid.geojson"),
            "x": context["village"].location.x,
            "y": context["village"].location.y,
            "loggedIn": self.request.user.is_authenticated,
        }
        return context

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class VillageCreateView(
    CampViewMixin,
    LoginRequiredMixin,
    CreateView,
):
    model = Village
    template_name = "village_form.html"
    fields = ["name", "description", "private", "location"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {"grid": static("json/grid.geojson")}
        return context

    def get_form(self, *args, **kwargs):
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

    def form_valid(self, form):
        village = form.save(commit=False)
        village.contact = self.request.user
        village.camp = self.camp
        if not village.name:
            village.name = "noname"
        village.save()
        messages.success(
            self.request,
            "Your request to create a village has been registered - it will be published after review for CoC compliance",
        )
        add_village_approve_email(village)
        return HttpResponseRedirect(village.get_absolute_url())

    def get_success_url(self):
        return reverse_lazy("village_list", kwargs={"camp_slug": self.object.camp.slug})


class EnsureUserOwnsVillageMixin(SingleObjectMixin):
    model = Village

    def dispatch(self, request, *args, **kwargs):
        # If the user is not contact for this village OR is not staff
        if not request.user.is_staff:
            if self.get_object().contact != request.user:
                raise Http404("Village not found")

        return super().dispatch(request, *args, **kwargs)


class VillageUpdateView(
    CampViewMixin,
    EnsureUserOwnsVillageMixin,
    LoginRequiredMixin,
    EnsureWritableCampMixin,
    UpdateView,
):
    model = Village
    template_name = "village_form.html"
    fields = ["name", "description", "private", "location"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mapData"] = {"grid": static("json/grid.geojson")}
        return context

    def get_form(self, *args, **kwargs):
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

    def form_valid(self, form):
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

    def get_success_url(self):
        return self.get_object().get_absolute_url()

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class VillageDeleteView(
    CampViewMixin,
    EnsureUserOwnsVillageMixin,
    LoginRequiredMixin,
    EnsureWritableCampMixin,
    DeleteView,
):
    model = Village
    template_name = "village_confirm_delete.html"
    context_object_name = "village"

    def get_success_url(self):
        return reverse_lazy("village_list", kwargs={"camp_slug": self.object.camp.slug})
