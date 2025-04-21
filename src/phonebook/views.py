import logging
import secrets
import string
import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic import View
from jsonview.views import JsonView
from oauth2_provider.views.generic import ScopedProtectedResourceView

from .mixins import DectRegistrationViewMixin
from .models import DectRegistration
from .dectutils import DectUtils
from .forms import DectRegistrationForm
from camps.mixins import CampViewMixin
from teams.models import Team
from utils.mixins import UserIsObjectOwnerMixin

logger = logging.getLogger("bornhack.%s" % __name__)
dectutil = DectUtils()


class DectExportJsonView(
    CampViewMixin,
    ScopedProtectedResourceView,
    JsonView,
):
    """
    JSON export for the POC team / DECT system
    """

    required_scopes = ["phonebook:read"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = Team.objects.get(name="POC", camp=self.camp)
        poc = self.request.user.has_perm("camps.poc_team_lead") and self.request.access_token.is_valid(
            ["phonebook:admin"],
        )
        context["phonebook"] = self.dump_phonebook(poc=poc)
        return context

    def dump_phonebook(self, poc: bool) -> list[DectRegistration]:
        """Dump phonebook for poc and non-poc use."""
        phonebook = []
        dects = DectRegistration.objects.filter(camp=self.camp)
        if not poc:
            # not a POC member, only return public numbers
            dects = dects.filter(publish_in_phonebook=True)
        # build list
        for dect in dects:
            entry = {
                "number": dect.number,
                "letters": dect.letters,
                "description": dect.description,
            }
            if poc:
                # POC member, include extra info
                ipei = None
                if dect.ipei:
                    ipei = dectutil.format_ipei(dect.ipei[0], dect.ipei[1])
                entry.update(
                    {
                        "activation_code": dect.activation_code,
                        "publish_in_phonebook": dect.publish_in_phonebook,
                        "ipei": ipei,
                    },
                )
            phonebook.append(entry)
        return phonebook


@method_decorator(csrf_exempt, name="dispatch")
class ApiDectUpdateIPEI(
    CampViewMixin,
    ScopedProtectedResourceView,
    View,
):
    """
    Function to update IPEI after user registered their phone on the network
    """

    required_scopes = ["phonebook:admin"]

    def post(self, request, dect_number, *args, **kwargs):
        team = Team.objects.get(name="POC", camp=self.camp)
        if not self.request.user.has_perm("camps.poc_team_lead") and self.request.access_token.is_valid(
            ["phonebook:admin"],
        ):
            return JsonResponse({"error": "Authentication failed"}, status=403)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        instance = get_object_or_404(
            DectRegistration,
            number=dect_number,
            camp=self.camp,
        )
        instance.ipei = data["ipei"]
        instance.save()
        return JsonResponse(
            {"message": "Record updated successfully", "data": data},
            status=200,
        )


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
    form_class = DectRegistrationForm
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

        try:
            dect.check_unique_ipei()
        except ValidationError as E:
            form.add_error("ipei", E)
            return super().form_invalid(form)

        # this check needs to be in this form, but not in model.save(), because then we cant save service numbers from the admin
        if len(dect.number) < 4:
            form.add_error(
                "number",
                ValidationError(
                    "Numbers with fewer than 4 digits are reserved for special use",
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
                "phonebook:dectregistration_list",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class DectRegistrationUpdateView(
    LoginRequiredMixin,
    DectRegistrationViewMixin,
    UserIsObjectOwnerMixin,
    UpdateView,
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
            self.request,
            "Your DECT registration has been updated successfully",
        )
        return redirect(
            reverse(
                "phonebook:dectregistration_list",
                kwargs={"camp_slug": self.camp.slug},
            ),
        )


class DectRegistrationDeleteView(
    LoginRequiredMixin,
    DectRegistrationViewMixin,
    UserIsObjectOwnerMixin,
    DeleteView,
):
    model = DectRegistration
    template_name = "dectregistration_delete.html"

    def get_success_url(self):
        messages.success(
            self.request,
            f"Your DECT registration for number {self.get_object().number} has been deleted successfully",
        )
        return reverse(
            "phonebook:dectregistration_list",
            kwargs={"camp_slug": self.camp.slug},
        )
