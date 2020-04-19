import csv
import logging
import secrets
import string

from camps.mixins import CampViewMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from oauth2_provider.views.generic import ProtectedResourceView
from utils.mixins import RaisePermissionRequiredMixin, UserIsObjectOwnerMixin

from .mixins import DectRegistrationViewMixin
from .models import DectRegistration

logger = logging.getLogger("bornhack.%s" % __name__)


class DectExportView(
    CampViewMixin, RaisePermissionRequiredMixin, ProtectedResourceView
):
    """
    CSV export for the POC team / DECT system
    """

    permission_required = "camps.pocteam_permission"

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{self.camp.slug}-dect-export-{timezone.now()}.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "number",
                "letters",
                "description",
                "activation_code",
                "publish_in_phonebook",
            ]
        )
        for dect in DectRegistration.objects.filter(camp=self.camp):
            writer.writerow(
                [
                    dect.number,
                    dect.letters,
                    dect.description,
                    dect.activation_code,
                    dect.publish_in_phonebook,
                ]
            )
        return response


class PhonebookListView(CampViewMixin, ListView):
    """
    Our phonebook view currently only shows DectRegistration entries,
    but could later be extended to show maybe GSM or other kinds of
    phone numbers.
    """

    model = DectRegistration
    template_name = "phonebook.html"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(publish_in_phonebook=True)


class DectRegistrationListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = DectRegistration
    template_name = "dectregistration_list.html"

    def get_queryset(self, *args, **kwargs):
        """
        Show only DectRegistration entries belonging to the current user
        """
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(user=self.request.user)


class DectRegistrationCreateView(LoginRequiredMixin, CampViewMixin, CreateView):
    model = DectRegistration
    fields = ["number", "letters", "description", "publish_in_phonebook"]
    template_name = "dectregistration_form.html"

    def form_valid(self, form):
        dect = form.save(commit=False)
        dect.camp = self.camp
        dect.user = self.request.user

        try:
            dect.clean_number()
        except ValidationError as E:
            form.add_error("number", E)
            return super().form_invalid(form)

        try:
            dect.clean_letters()
        except ValidationError as E:
            form.add_error("letters", E)
            return super().form_invalid(form)

        # this check needs to be in this form, but not in model.save(), because then we cant save service numbers from the admin
        if len(dect.number) < 4:
            form.add_error(
                "number",
                ValidationError(
                    "Numbers with fewer than 4 digits are reserved for special use"
                ),
            )
            return super().form_invalid(form)

        # generate a 10 digit activation code for this dect registration?
        if not dect.activation_code:
            dect.activation_code = "".join(
                secrets.choice(string.digits) for i in range(10)
            )

        # all good, save and return to list
        dect.save()
        messages.success(
            self.request,
            "New DECT registration created successfully. Call the activation number from your handset to activate it!",
        )
        return redirect(
            reverse(
                "phonebook:dectregistration_list", kwargs={"camp_slug": self.camp.slug}
            )
        )


class DectRegistrationUpdateView(
    LoginRequiredMixin, DectRegistrationViewMixin, UserIsObjectOwnerMixin, UpdateView
):
    model = DectRegistration
    fields = ["letters", "description", "publish_in_phonebook"]
    template_name = "dectregistration_form.html"

    def form_valid(self, form):
        dect = form.save(commit=False)

        # check if the letters match the DECT number
        try:
            dect.clean_letters()
        except ValidationError as E:
            form.add_error("letters", E)
            return super().form_invalid(form)

        # save and return
        dect.save()
        messages.success(
            self.request, "Your DECT registration has been updated successfully"
        )
        return redirect(
            reverse(
                "phonebook:dectregistration_list", kwargs={"camp_slug": self.camp.slug}
            )
        )


class DectRegistrationDeleteView(
    LoginRequiredMixin, DectRegistrationViewMixin, UserIsObjectOwnerMixin, DeleteView
):
    model = DectRegistration
    template_name = "dectregistration_delete.html"

    def get_success_url(self):
        messages.success(
            self.request,
            f"Your DECT registration for number {self.get_object().number} has been deleted successfully",
        )
        return reverse(
            "phonebook:dectregistration_list", kwargs={"camp_slug": self.camp.slug}
        )
