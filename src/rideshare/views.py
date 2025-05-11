from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from camps.mixins import CampViewMixin
from teams.models import Team
from utils.email import add_outgoing_email
from utils.mixins import UserIsObjectOwnerMixin

from .models import Ride


class ContactRideForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Remember to include your contact information!"},
        ),
        label="Write a message to the author of this rideshare",
        help_text="ATTENTION!: Pressing send will send an email to the author with the above text. It is up to you to include your contact information in the message so the person receiving the email can contact you.",
    )


class RideList(LoginRequiredMixin, CampViewMixin, ListView):
    model = Ride


class RideDetail(LoginRequiredMixin, CampViewMixin, DetailView):
    model = Ride

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ContactRideForm()
        return context

    def post(self, request, **kwargs):
        form = ContactRideForm(request.POST)
        if form.is_valid():
            ride = self.get_object()
            info_team = Team.objects.get(camp=self.camp, name="Info")
            add_outgoing_email(
                responsible_team=info_team,
                text_template="rideshare/emails/contact_mail.txt",
                to_recipients=[ride.user.emailaddress_set.get(primary=True).email],
                formatdict={
                    "rideshare_url": "https://bornhack.dk{}".format(
                        reverse(
                            "rideshare:detail",
                            kwargs={"camp_slug": self.camp.slug, "pk": ride.pk},
                        ),
                    ),
                    "message": form.cleaned_data["message"],
                },
                subject="BornHack rideshare message!",
            )
        messages.info(request, "Your message has been sent.")
        return HttpResponseRedirect(ride.get_absolute_url())


class RideCreate(LoginRequiredMixin, CampViewMixin, CreateView):
    model = Ride
    fields = [
        "author",
        "has_car",
        "from_location",
        "to_location",
        "when",
        "seats",
        "description",
    ]

    def get_initial(self):
        """Default 'author' to users public_credit_name where relevant"""
        return {"author": self.request.user.profile.get_public_credit_name}

    def form_valid(self, form, **kwargs):
        """Set camp and user before saving"""
        ride = form.save(commit=False)
        ride.camp = self.camp
        ride.user = self.request.user
        ride.save()
        self.object = ride
        return HttpResponseRedirect(self.get_success_url())


class RideUpdate(LoginRequiredMixin, CampViewMixin, UserIsObjectOwnerMixin, UpdateView):
    model = Ride
    fields = [
        "author",
        "has_car",
        "from_location",
        "to_location",
        "when",
        "seats",
        "description",
    ]


class RideDelete(LoginRequiredMixin, CampViewMixin, UserIsObjectOwnerMixin, DeleteView):
    model = Ride

    def get_success_url(self):
        return reverse("rideshare:list", kwargs={"camp_slug": self.camp.slug})
