from __future__ import annotations

import os

import magic
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView

from camps.mixins import CampViewMixin
from teams.models import Team
from utils.email import add_outgoing_email
from utils.mixins import RaisePermissionRequiredMixin
from utils.mixins import VerbCreateView as CreateView
from utils.mixins import VerbUpdateView as UpdateView

from .forms import ExpenseCreateForm
from .forms import ExpenseUpdateForm
from .forms import RevenueCreateForm
from .forms import RevenueUpdateForm
from .mixins import ChainViewMixin
from .mixins import CredebtorViewMixin
from .mixins import ExpensePermissionMixin
from .mixins import ReimbursementPermissionMixin
from .mixins import ReimbursementUnpaidMixin
from .mixins import RevenuePermissionMixin
from .models import Chain
from .models import Credebtor
from .models import Expense
from .models import Reimbursement
from .models import Revenue


class EconomyDashboardView(LoginRequiredMixin, CampViewMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        """Add expenses, reimbursements and revenues to the context"""
        context = super().get_context_data(**kwargs)

        # get reimbursement stats
        context["reimbursement_count"] = Reimbursement.objects.filter(
            reimbursement_user=self.request.user,
            camp=self.camp,
        ).count()
        context["unpaid_reimbursement_count"] = Reimbursement.objects.filter(
            reimbursement_user=self.request.user,
            paid=False,
            camp=self.camp,
        ).count()
        context["paid_reimbursement_count"] = Reimbursement.objects.filter(
            reimbursement_user=self.request.user,
            paid=True,
            camp=self.camp,
        ).count()
        reimbursement_total = 0
        for reimbursement in Reimbursement.objects.filter(
            reimbursement_user=self.request.user,
            camp=self.camp,
        ):
            reimbursement_total += reimbursement.amount
        context["reimbursement_total"] = reimbursement_total

        # get expense stats
        context["expense_count"] = Expense.objects.filter(
            user=self.request.user,
            camp=self.camp,
        ).count()
        context["unapproved_expense_count"] = Expense.objects.filter(
            user=self.request.user,
            approved__isnull=True,
            camp=self.camp,
        ).count()
        context["approved_expense_count"] = Expense.objects.filter(
            user=self.request.user,
            approved=True,
            camp=self.camp,
        ).count()
        context["rejected_expense_count"] = Expense.objects.filter(
            user=self.request.user,
            approved=False,
            camp=self.camp,
        ).count()
        context["expense_total"] = Expense.objects.filter(
            user=self.request.user,
            camp=self.camp,
        ).aggregate(Sum("amount"))["amount__sum"]

        # get revenue stats
        context["revenue_count"] = Revenue.objects.filter(
            user=self.request.user,
            camp=self.camp,
        ).count()
        context["unapproved_revenue_count"] = Revenue.objects.filter(
            user=self.request.user,
            approved__isnull=True,
            camp=self.camp,
        ).count()
        context["approved_revenue_count"] = Revenue.objects.filter(
            user=self.request.user,
            approved=True,
            camp=self.camp,
        ).count()
        context["rejected_revenue_count"] = Revenue.objects.filter(
            user=self.request.user,
            approved=False,
            camp=self.camp,
        ).count()
        context["revenue_total"] = Revenue.objects.filter(
            user=self.request.user,
            camp=self.camp,
        ).aggregate(Sum("amount"))["amount__sum"]

        return context


############################################
# Chain/Credebtor related views


class ChainCreateView(CampViewMixin, RaisePermissionRequiredMixin, CreateView):
    model = Chain
    template_name = "chain_create.html"
    permission_required = "camps.expense_create_permission"
    fields = ["name", "notes"]

    def form_valid(self, form):
        chain = form.save()

        # a message for the user
        messages.success(
            self.request,
            "The new Chain %s has been saved. You can now add Creditor(s)/Debtor(s) for it." % chain.name,
        )

        return HttpResponseRedirect(
            reverse(
                "economy:credebtor_create",
                kwargs={"camp_slug": self.camp.slug, "chain_slug": chain.slug},
            ),
        )


class ChainListView(CampViewMixin, RaisePermissionRequiredMixin, ListView):
    model = Chain
    template_name = "chain_list.html"
    permission_required = "camps.expense_create_permission"


class CredebtorCreateView(
    CampViewMixin,
    ChainViewMixin,
    RaisePermissionRequiredMixin,
    CreateView,
):
    model = Credebtor
    template_name = "credebtor_create.html"
    permission_required = "camps.expense_create_permission"
    fields = ["name", "address", "notes"]

    def get_context_data(self, **kwargs):
        """Add chain to context"""
        context = super().get_context_data(**kwargs)
        context["chain"] = self.chain
        return context

    def form_valid(self, form):
        credebtor = form.save(commit=False)
        credebtor.chain = self.chain
        credebtor.save()

        # a message for the user
        messages.success(
            self.request,
            "The Creditor/Debtor %s has been saved. You can now add Expenses/Revenues for it." % credebtor.name,
        )

        return HttpResponseRedirect(
            reverse(
                "economy:credebtor_list",
                kwargs={"camp_slug": self.camp.slug, "chain_slug": self.chain.slug},
            ),
        )


class CredebtorListView(
    CampViewMixin,
    ChainViewMixin,
    RaisePermissionRequiredMixin,
    ListView,
):
    model = Credebtor
    template_name = "credebtor_list.html"
    permission_required = "camps.expense_create_permission"

    def get_context_data(self, **kwargs):
        """Add chain to context"""
        context = super().get_context_data(**kwargs)
        context["chain"] = self.chain
        return context


############################################
# Expense related views


class ExpenseListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = Expense
    template_name = "expense_list.html"

    def get_queryset(self):
        # only return Expenses belonging to the current user
        return super().get_queryset().filter(user=self.request.user)


class ExpenseDetailView(CampViewMixin, ExpensePermissionMixin, DetailView):
    model = Expense
    template_name = "expense_detail.html"


class ExpenseCreateView(
    CampViewMixin,
    CredebtorViewMixin,
    RaisePermissionRequiredMixin,
    CreateView,
):
    model = Expense
    template_name = "expense_form.html"
    permission_required = "camps.expense_create_permission"
    form_class = ExpenseCreateForm

    def get_context_data(self, **kwargs):
        """Do not show teams that are not part of the current camp in the dropdown"""
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = Team.objects.filter(
            camp=self.camp,
        )
        context["creditor"] = self.credebtor
        return context

    def form_valid(self, form):
        expense = form.save(commit=False)
        expense.user = self.request.user
        expense.camp = self.camp
        expense.creditor = self.credebtor
        expense.save()

        # a message for the user
        messages.success(
            self.request,
            "The expense has been saved. It is now awaiting approval by the economy team.",
        )

        # send an email to the economy team
        add_outgoing_email(
            responsible_team=Team.objects.get(
                camp=self.camp,
                name=settings.ECONOMY_TEAM_NAME,
            ),
            text_template="emails/expense_awaiting_approval_email.txt",
            formatdict={"expense": expense},
            subject="New %s expense for %s Team is awaiting approval"
            % (expense.camp.title, expense.responsible_team.name),
            to_recipients=[settings.ECONOMYTEAM_EMAIL],
        )

        # return to the expense list page
        return HttpResponseRedirect(
            reverse("economy:expense_list", kwargs={"camp_slug": self.camp.slug}),
        )


class ExpenseUpdateView(CampViewMixin, ExpensePermissionMixin, UpdateView):
    model = Expense
    template_name = "expense_form.html"
    form_class = ExpenseUpdateForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.get_object().approved:
            messages.error(
                self.request,
                "This expense has already been approved, it cannot be updated",
            )
            return redirect(
                reverse("economy:expense_list", kwargs={"camp_slug": self.camp.slug}),
            )
        return response

    def get_context_data(self, **kwargs):
        """Do not show teams that are not part of the current camp in the dropdown"""
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = Team.objects.filter(
            camp=self.camp,
        )
        context["creditor"] = self.get_object().creditor
        return context

    def get_success_url(self):
        messages.success(
            self.request,
            "Expense %s has been updated" % self.get_object().pk,
        )
        return reverse("economy:expense_list", kwargs={"camp_slug": self.camp.slug})


class ExpenseDeleteView(CampViewMixin, ExpensePermissionMixin, UpdateView):
    model = Expense
    template_name = "expense_delete.html"
    fields = []

    def form_valid(self, form):
        expense = self.get_object()
        if expense.approved:
            messages.error(
                self.request,
                "This expense has already been approved, it cannot be deleted",
            )
        else:
            message = "Expense %s has been deleted" % expense.pk
            expense.delete()
            messages.success(self.request, message)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("economy:expense_list", kwargs={"camp_slug": self.camp.slug})


class ExpenseInvoiceView(CampViewMixin, ExpensePermissionMixin, DetailView):
    """This view returns the invoice for an Expense with the proper mimetype
    Uses ExpensePermissionMixin to make sure the user is allowed to see the image
    """

    model = Expense

    def get(self, request, *args, **kwargs):
        # get expense
        expense = self.get_object()
        # read invoice file
        invoicedata = expense.invoice.read()
        # find mimetype
        mimetype = magic.from_buffer(invoicedata, mime=True)
        # check if we have a PDF, no preview if so, load a pdf icon instead
        if mimetype == "application/pdf" and "preview" in request.GET:
            invoicedata = open(
                os.path.join(settings.BASE_DIR, "static_src/img/pdf.png"),
                "rb",
            ).read()
            mimetype = magic.from_buffer(invoicedata, mime=True)
        # put the response together and return it
        response = HttpResponse(content_type=mimetype)
        response.write(invoicedata)
        return response


############################################
# Reimbursement related views


class ReimbursementListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = Reimbursement
    template_name = "reimbursement_list.html"

    def get_queryset(self):
        # only return Expenses belonging to the current user
        return super().get_queryset().filter(reimbursement_user=self.request.user)


class ReimbursementDetailView(CampViewMixin, ReimbursementPermissionMixin, DetailView):
    model = Reimbursement
    template_name = "reimbursement_detail.html"


class ReimbursementCreateView(CampViewMixin, ExpensePermissionMixin, CreateView):
    model = Reimbursement
    template_name = "reimbursement_form.html"
    fields = ["bank_account"]

    def get(self, request, *args, **kwargs):
        """Check if this user has any approved and un-reimbursed expenses."""
        if not request.user.expenses.filter(
            reimbursement__isnull=True,
            approved=True,
            paid_by_bornhack=False,
        ):
            messages.error(
                request,
                "You have no approved and unreimbursed expenses!",
            )
            return redirect(
                reverse("economy:dashboard", kwargs={"camp_slug": self.camp.slug}),
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expenses"] = Expense.objects.filter(
            user=self.request.user,
            approved=True,
            reimbursement__isnull=True,
            paid_by_bornhack=False,
        )
        context["total_amount"] = context["expenses"].aggregate(Sum("amount"))
        context["reimbursement_user"] = self.request.user
        context["cancelurl"] = reverse(
            "economy:reimbursement_list",
            kwargs={"camp_slug": self.camp.slug},
        )
        return context

    def form_valid(self, form):
        """Set user and camp for the Reimbursement before saving"""
        # get the expenses for this user
        expenses = Expense.objects.filter(
            user=self.request.user,
            approved=True,
            reimbursement__isnull=True,
            paid_by_bornhack=False,
        )
        if not expenses:
            messages.error(self.request, "No expenses found")
            return redirect(
                reverse("economy:dashboard", kwargs={"camp_slug": self.camp.slug}),
            )

        # do we have an Economy team for this camp?
        if not self.camp.economy_team:
            messages.error(self.request, "No economy team found")
            return redirect(
                reverse("economy:dashboard", kwargs={"camp_slug": self.camp.slug}),
            )

        # create reimbursement in database
        reimbursement = form.save(commit=False)
        reimbursement.reimbursement_user = self.request.user
        reimbursement.user = self.request.user
        reimbursement.camp = self.camp
        reimbursement.save()

        # add all expenses to reimbursement
        for expense in expenses:
            expense.reimbursement = reimbursement
            expense.save()

        # create payback expense for this reimbursement
        reimbursement.create_payback_expense()

        messages.success(
            self.request,
            f"Reimbursement {reimbursement.pk} has been created. It will be paid by the economy team to the specified bank account.",
        )

        # send an email to the economy team
        add_outgoing_email(
            responsible_team=Team.objects.get(
                camp=self.camp,
                name=settings.ECONOMY_TEAM_NAME,
            ),
            text_template="emails/reimbursement_created.txt",
            formatdict={"reimbursement": reimbursement},
            subject=f"New {self.camp.title} reimbursement {reimbursement.pk} for user {reimbursement.reimbursement_user.username} created",
            to_recipients=[settings.ECONOMYTEAM_EMAIL],
        )

        return redirect(
            reverse(
                "economy:reimbursement_detail",
                kwargs={"camp_slug": self.camp.slug, "pk": reimbursement.pk},
            ),
        )


class ReimbursementUpdateView(
    CampViewMixin,
    ReimbursementPermissionMixin,
    ReimbursementUnpaidMixin,
    UpdateView,
):
    model = Reimbursement
    template_name = "reimbursement_form.html"
    fields = ["bank_account"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expenses"] = self.object.expenses.filter(paid_by_bornhack=False)
        context["total_amount"] = context["expenses"].aggregate(Sum("amount"))
        context["reimbursement_user"] = self.request.user
        context["cancelurl"] = reverse(
            "economy:reimbursement_list",
            kwargs={"camp_slug": self.camp.slug},
        )
        return context

    def get_success_url(self):
        return reverse(
            "economy:reimbursement_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.get_object().pk},
        )


class ReimbursementDeleteView(
    CampViewMixin,
    ReimbursementPermissionMixin,
    ReimbursementUnpaidMixin,
    DeleteView,
):
    model = Reimbursement
    template_name = "reimbursement_delete.html"

    def get_success_url(self):
        messages.success(
            self.request,
            f"Reimbursement {self.kwargs['pk']} deleted successfully!",
        )
        return reverse(
            "economy:reimbursement_list",
            kwargs={"camp_slug": self.camp.slug},
        )


############################################
# Revenue related views


class RevenueListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = Revenue
    template_name = "revenue_list.html"

    def get_queryset(self):
        # only return Revenues belonging to the current user
        return super().get_queryset().filter(user=self.request.user)


class RevenueDetailView(CampViewMixin, RevenuePermissionMixin, DetailView):
    model = Revenue
    template_name = "revenue_detail.html"


class RevenueCreateView(
    CampViewMixin,
    CredebtorViewMixin,
    RaisePermissionRequiredMixin,
    CreateView,
):
    model = Revenue
    template_name = "revenue_form.html"
    permission_required = "camps.revenue_create_permission"
    form_class = RevenueCreateForm

    def get_context_data(self, **kwargs):
        """Do not show teams that are not part of the current camp in the dropdown"""
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = Team.objects.filter(
            camp=self.camp,
        )
        context["debtor"] = self.credebtor
        return context

    def form_valid(self, form):
        revenue = form.save(commit=False)
        revenue.user = self.request.user
        revenue.camp = self.camp
        revenue.debtor = self.credebtor
        revenue.save()

        # a message for the user
        messages.success(
            self.request,
            "The revenue has been saved. It is now awaiting approval by the economy team.",
        )

        # send an email to the economy team
        add_outgoing_email(
            responsible_team=Team.objects.get(
                camp=self.camp,
                name=settings.ECONOMY_TEAM_NAME,
            ),
            text_template="emails/revenue_awaiting_approval_email.txt",
            formatdict={"revenue": revenue},
            subject="New %s revenue for %s Team is awaiting approval"
            % (revenue.camp.title, revenue.responsible_team.name),
            to_recipients=[settings.ECONOMYTEAM_EMAIL],
        )

        # return to the revenue list page
        return HttpResponseRedirect(
            reverse("economy:revenue_list", kwargs={"camp_slug": self.camp.slug}),
        )


class RevenueUpdateView(CampViewMixin, RevenuePermissionMixin, UpdateView):
    model = Revenue
    template_name = "revenue_form.html"
    form_class = RevenueUpdateForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.get_object().approved:
            messages.error(
                self.request,
                "This revenue has already been approved, it cannot be updated",
            )
            return redirect(
                reverse("economy:revenue_list", kwargs={"camp_slug": self.camp.slug}),
            )
        return response

    def get_context_data(self, **kwargs):
        """Do not show teams that are not part of the current camp in the dropdown"""
        context = super().get_context_data(**kwargs)
        context["form"].fields["responsible_team"].queryset = Team.objects.filter(
            camp=self.camp,
        )
        return context

    def get_success_url(self):
        messages.success(
            self.request,
            "Revenue %s has been updated" % self.get_object().pk,
        )
        return reverse("economy:revenue_list", kwargs={"camp_slug": self.camp.slug})


class RevenueDeleteView(CampViewMixin, RevenuePermissionMixin, UpdateView):
    model = Revenue
    template_name = "revenue_delete.html"
    fields = []

    def form_valid(self, form):
        revenue = self.get_object()
        if revenue.approved:
            messages.error(
                self.request,
                "This revenue has already been approved, it cannot be deleted",
            )
        else:
            message = "Revenue %s has been deleted" % revenue.pk
            revenue.delete()
            messages.success(self.request, message)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("economy:revenue_list", kwargs={"camp_slug": self.camp.slug})


class RevenueInvoiceView(CampViewMixin, RevenuePermissionMixin, DetailView):
    """This view returns a http response with the invoice for a Revenue object, with the proper mimetype
    Uses RevenuePermissionMixin to make sure the user is allowed to see the file
    """

    model = Revenue

    def get(self, request, *args, **kwargs):
        # get revenue
        revenue = self.get_object()
        # read invoice file
        invoicedata = revenue.invoice.read()
        # find mimetype
        mimetype = magic.from_buffer(invoicedata, mime=True)
        # check if we have a PDF, no preview if so, load a pdf icon instead
        if mimetype == "application/pdf" and "preview" in request.GET:
            invoicedata = open(
                os.path.join(settings.BASE_DIR, "static_src/img/pdf.png"),
                "rb",
            ).read()
            mimetype = magic.from_buffer(invoicedata, mime=True)
        # put the response together and return it
        response = HttpResponse(content_type=mimetype)
        response.write(invoicedata)
        return response
