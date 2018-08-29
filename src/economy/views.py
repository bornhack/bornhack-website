import magic

from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.urls import reverse
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin

from camps.mixins import CampViewMixin
from utils.email import add_outgoing_email
from utils.mixins import RaisePermissionRequiredMixin
from teams.models import Team
from .models import Expense, Reimbursement
from .mixins import ExpensePermissionMixin, ReimbursementPermissionMixin


class ExpenseListView(LoginRequiredMixin, CampViewMixin, ListView):
    model = Expense
    template_name = 'expense_list.html'

    def get_queryset(self):
        # only return Expenses belonging to the current user
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        """
        Add reimbursements to the context
        """
        context = super().get_context_data(**kwargs)
        context['reimbursement_list'] = Reimbursement.objects.filter(user=self.request.user)
        return context


class ExpenseDetailView(CampViewMixin, ExpensePermissionMixin, DetailView):
    model = Expense
    template_name = 'expense_detail.html'
    pk_url_kwarg = 'expense_uuid'


class ExpenseCreateView(CampViewMixin, RaisePermissionRequiredMixin, CreateView):
    model = Expense
    fields = ['description', 'amount', 'invoice', 'paid_by_bornhack', 'responsible_team'] 
    template_name = 'expense_form.html'
    permission_required = ("camps.expense_create_permission")

    def get_context_data(self, **kwargs):
        """
        Do not show teams that are not part of the current camp in the dropdown
        """
        context = super().get_context_data(**kwargs)
        context['form'].fields['responsible_team'].queryset = Team.objects.filter(camp=self.camp)
        return context

    def form_valid(self, form):
        # TODO: make sure this user has permission to create expenses
        expense = form.save(commit=False)
        expense.user = self.request.user
        expense.camp = self.camp
        expense.save()

        # a message for the user
        messages.success(
            self.request,
            "The expense has been saved. It is now awaiting approval by the economy team.",
        )

        # send an email to the economy team
        add_outgoing_email(
            "emails/expense_awaiting_approval_email.txt",
            formatdict=dict(expense=expense),
            subject="New %s expense for %s Team is awaiting approval" % (expense.camp.title, expense.responsible_team.name),
            to_recipients=[settings.ECONOMYTEAM_EMAIL],
        )

        # return to the expense list page
        return HttpResponseRedirect(reverse('economy:expense_list', kwargs={'camp_slug': self.camp.slug}))


class ExpenseInvoiceView(CampViewMixin, ExpensePermissionMixin, DetailView):
    """
    This view returns the invoice for an Expense with the proper mimetype
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
        # put the response together and return it
        response = HttpResponse(content_type=mimetype)
        response.write(invoicedata)
        return response


class ReimbursementDetailView(CampViewMixin, ReimbursementPermissionMixin, DetailView):
    model = Reimbursement
    template_name = 'reimbursement_detail.html'

