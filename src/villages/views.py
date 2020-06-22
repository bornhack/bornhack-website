from camps.mixins import CampViewMixin
from camps.models import Camp
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from .mixins import EnsureWritableCampMixin
from .models import Village


class VillageListView(CampViewMixin, ListView):
    model = Village
    template_name = "village_list.html"
    context_object_name = "villages"

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class VillageDetailView(CampViewMixin, DetailView):
    model = Village
    template_name = "village_detail.html"
    context_object_name = "village"

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class VillageCreateView(
    CampViewMixin, LoginRequiredMixin, EnsureWritableCampMixin, CreateView
):
    model = Village
    template_name = "village_form.html"
    fields = ["name", "description", "private"]

    def form_valid(self, form):
        village = form.save(commit=False)
        village.contact = self.request.user
        village.camp = Camp.objects.get(slug=self.request.session["campslug"])
        if not village.name:
            village.name = "noname"
        village.save()
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

        return super(EnsureUserOwnsVillageMixin, self).dispatch(
            request, *args, **kwargs
        )


class VillageUpdateView(
    CampViewMixin,
    EnsureUserOwnsVillageMixin,
    LoginRequiredMixin,
    EnsureWritableCampMixin,
    UpdateView,
):
    model = Village
    template_name = "village_form.html"
    fields = ["name", "description", "private"]

    def form_valid(self, form):
        village = form.save(commit=False)
        if not village.name:
            village.name = "noname"
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
