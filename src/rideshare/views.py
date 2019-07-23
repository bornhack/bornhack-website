from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.http import HttpResponseRedirect
from django import forms

from camps.mixins import CampViewMixin
from utils.email import add_outgoing_email

from .models import Ride


class ContactRideForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Remember to include your contact information!"}
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
            add_outgoing_email(
                text_template="rideshare/emails/contact_mail.txt",
                to_recipients=[ride.user.emailaddress_set.get(primary=True).email],
                formatdict=dict(
                    rideshare_url="https://bornhack.dk{}".format(
                        reverse(
                            "rideshare:detail",
                            kwargs={"camp_slug": self.camp.slug, "pk": ride.pk},
                        )
                    ),
                    message=form.cleaned_data["message"],
                ),
                subject="BornHack rideshare message!",
            )
        messages.info(request, "Your message has been sent.")
        return HttpResponseRedirect(ride.get_absolute_url())


class RideCreate(LoginRequiredMixin, CampViewMixin, CreateView):
    model = Ride
    fields = ["author", "has_car", "from_location", "to_location", "when", "seats", "description"]

    def get_initial(self):
        """
        Default 'author' to users public_credit_name where relevant
        """
        return {
            "author": self.request.user.profile.get_public_credit_name
        }

    def form_valid(self, form, **kwargs):
        """
        Set camp and user before saving
        """
        ride = form.save(commit=False)
        ride.camp = self.camp
        ride.user = self.request.user
        ride.save()
        self.object = ride
        return HttpResponseRedirect(self.get_success_url())


class IsRideOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().user == self.request.user


class RideUpdate(LoginRequiredMixin, CampViewMixin, IsRideOwnerMixin, UpdateView):
    model = Ride
    fields = ["author", "has_car", "from_location", "to_location", "when", "seats", "description"]


class RideDelete(LoginRequiredMixin, CampViewMixin, IsRideOwnerMixin, DeleteView):
    model = Ride

    def get_success_url(self):
        return reverse("rideshare:list", kwargs={"camp_slug": self.camp.slug})
