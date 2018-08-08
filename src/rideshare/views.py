from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.http import HttpResponseRedirect

from camps.mixins import CampViewMixin

from .models import Ride


class RideList(LoginRequiredMixin, CampViewMixin, ListView):
    model = Ride


class RideDetail(LoginRequiredMixin, CampViewMixin, DetailView):
    model = Ride


class RideCreate(LoginRequiredMixin, CampViewMixin, CreateView):
    model = Ride
    fields = ['location', 'when', 'seats', 'description']

    def form_valid(self, form, **kwargs):
        ride = form.save(commit=False)
        ride.camp = self.camp
        ride.user = self.request.user
        ride.save()
        self.object = ride
        return HttpResponseRedirect(self.get_success_url())


class RideUpdate(LoginRequiredMixin, CampViewMixin, UpdateView):
    model = Ride
    fields = ['location', 'when', 'seats', 'description']


class RideDelete(LoginRequiredMixin, CampViewMixin, DeleteView):
    model = Ride
