import logging
import os
from itertools import chain

import requests
from camps.mixins import CampViewMixin
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.db.models import Sum
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from economy.models import Chain, Credebtor, Expense, Reimbursement, Revenue
from facilities.models import FacilityFeedback
from profiles.models import Profile
from program.models import EventFeedback, EventProposal, SpeakerProposal
from shop.models import Order, OrderProductRelation
from teams.models import Team
from tickets.models import DiscountTicket, ShopTicket, SponsorTicket, TicketType

from .mixins import (
    ContentTeamPermissionMixin,
    EconomyTeamPermissionMixin,
    InfoTeamPermissionMixin,
    OrgaTeamPermissionMixin,
    RaisePermissionRequiredMixin,
)

logger = logging.getLogger("bornhack.%s" % __name__)


class BackofficeIndexView(CampViewMixin, RaisePermissionRequiredMixin, TemplateView):
    """
    The Backoffice index view only requires camps.backoffice_permission so we use RaisePermissionRequiredMixin directly
    """

    permission_required = "camps.backoffice_permission"
    template_name = "index.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["facilityfeedback_teams"] = Team.objects.filter(
            id__in=set(
                FacilityFeedback.objects.filter(
                    facility__facility_type__responsible_team__camp=self.camp,
                    handled=False,
                ).values_list(
                    "facility__facility_type__responsible_team__id", flat=True
                )
            )
        )
        return context


class FacilityFeedbackView(CampViewMixin, RaisePermissionRequiredMixin, FormView):
    template_name = "facilityfeedback_backoffice.html"

    def get_permission_required(self):
        """
        This view requires two permissions, camps.backoffice_permission and
        the permission_set for the team in question.
        """
        if not self.team.permission_set:
            raise PermissionDenied("No permissions set defined for this team")
        return ["camps.backoffice_permission", self.team.permission_set]

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.team = get_object_or_404(
            Team, camp=self.camp, slug=self.kwargs["team_slug"]
        )
        self.queryset = FacilityFeedback.objects.filter(
            facility__facility_type__responsible_team=self.team, handled=False
        )
        self.form_class = modelformset_factory(
            FacilityFeedback,
            fields=("handled",),
            min_num=self.queryset.count(),
            validate_min=True,
            max_num=self.queryset.count(),
            validate_max=True,
            extra=0,
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["team"] = self.team
        context["feedback_list"] = self.queryset
        context["formset"] = self.form_class(queryset=self.queryset)
        return context

    def form_valid(self, form):
        form.save()
        if form.changed_objects:
            messages.success(
                self.request,
                f"Marked {len(form.changed_objects)} FacilityFeedbacks as handled!",
            )
        return redirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "backoffice:facilityfeedback",
            kwargs={"camp_slug": self.camp.slug, "team_slug": self.team.slug},
        )


class ProductHandoutView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "product_handout.html"

    def get_queryset(self, **kwargs):
        return OrderProductRelation.objects.filter(
            ticket_generated=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
        ).order_by("order")


class BadgeHandoutView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "badge_handout.html"
    context_object_name = "tickets"

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(badge_ticket_generated=False)
        sponsortickets = SponsorTicket.objects.filter(badge_ticket_generated=False)
        discounttickets = DiscountTicket.objects.filter(badge_ticket_generated=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class TicketCheckinView(CampViewMixin, InfoTeamPermissionMixin, ListView):
    template_name = "ticket_checkin.html"
    context_object_name = "tickets"

    def get_queryset(self, **kwargs):
        shoptickets = ShopTicket.objects.filter(used=False)
        sponsortickets = SponsorTicket.objects.filter(used=False)
        discounttickets = DiscountTicket.objects.filter(used=False)
        return list(chain(shoptickets, sponsortickets, discounttickets))


class ApproveNamesView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    template_name = "approve_public_credit_names.html"
    context_object_name = "profiles"

    def get_queryset(self, **kwargs):
        return Profile.objects.filter(public_credit_name_approved=False).exclude(
            public_credit_name=""
        )


class ApproveFeedbackView(CampViewMixin, ContentTeamPermissionMixin, FormView):
    """
    This view shows a list of EventFeedback objects which are pending approval.
    """

    model = EventFeedback
    template_name = "approve_feedback.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.queryset = EventFeedback.objects.filter(
            event__track__camp=self.camp, approved__isnull=True
        )

        self.form_class = modelformset_factory(
            EventFeedback,
            fields=("approved",),
            min_num=self.queryset.count(),
            validate_min=True,
            max_num=self.queryset.count(),
            validate_max=True,
            extra=0,
        )

    def get_context_data(self, *args, **kwargs):
        """
        Include the queryset used for the modelformset_factory so we have
        some idea which object is which in the template
        Why the hell do the forms in the formset not include the object?
        """
        context = super().get_context_data(*args, **kwargs)
        context["eventfeedback_list"] = self.queryset
        context["formset"] = self.form_class(queryset=self.queryset)
        return context

    def form_valid(self, form):
        form.save()
        if form.changed_objects:
            messages.success(
                self.request, f"Updated {len(form.changed_objects)} EventFeedbacks"
            )
        return redirect(self.get_success_url())

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "backoffice:approve_eventfeedback", kwargs={"camp_slug": self.camp.slug}
        )


class ManageProposalsView(CampViewMixin, ContentTeamPermissionMixin, ListView):
    """
    This view shows a list of pending SpeakerProposal and EventProposals.
    """

    template_name = "manage_proposals.html"
    context_object_name = "speakerproposals"

    def get_queryset(self, **kwargs):
        return SpeakerProposal.objects.filter(
            camp=self.camp, proposal_status=SpeakerProposal.PROPOSAL_PENDING
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["eventproposals"] = EventProposal.objects.filter(
            track__camp=self.camp, proposal_status=EventProposal.PROPOSAL_PENDING
        )
        return context


class ProposalManageBaseView(CampViewMixin, ContentTeamPermissionMixin, UpdateView):
    """
    This class contains the shared logic between SpeakerProposalManageView and EventProposalManageView
    """

    fields = ["reason"]

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        if "approve" in form.data:
            # approve button was pressed
            form.instance.mark_as_approved(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            form.instance.mark_as_rejected(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse("backoffice:manage_proposals", kwargs={"camp_slug": self.camp.slug})
        )


class SpeakerProposalManageView(ProposalManageBaseView):
    """
    This view allows an admin to approve/reject SpeakerProposals
    """

    model = SpeakerProposal
    template_name = "manage_speakerproposal.html"


class EventProposalManageView(ProposalManageBaseView):
    """
    This view allows an admin to approve/reject EventProposals
    """

    model = EventProposal
    template_name = "manage_eventproposal.html"


class MerchandiseOrdersView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    template_name = "orders_merchandise.html"

    def get_queryset(self, **kwargs):
        camp_prefix = "BornHack {}".format(timezone.now().year)

        return (
            OrderProductRelation.objects.filter(
                ticket_generated=False,
                order__paid=True,
                order__refunded=False,
                order__cancelled=False,
                product__category__name="Merchandise",
            )
            .filter(product__name__startswith=camp_prefix)
            .order_by("order")
        )


class MerchandiseToOrderView(CampViewMixin, OrgaTeamPermissionMixin, TemplateView):
    template_name = "merchandise_to_order.html"

    def get_context_data(self, **kwargs):
        camp_prefix = "BornHack {}".format(timezone.now().year)

        order_relations = OrderProductRelation.objects.filter(
            ticket_generated=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
            product__category__name="Merchandise",
        ).filter(product__name__startswith=camp_prefix)

        merchandise_orders = {}
        for relation in order_relations:
            try:
                quantity = merchandise_orders[relation.product.name] + relation.quantity
                merchandise_orders[relation.product.name] = quantity
            except KeyError:
                merchandise_orders[relation.product.name] = relation.quantity

        context = super().get_context_data(**kwargs)
        context["merchandise"] = merchandise_orders
        return context


class VillageOrdersView(CampViewMixin, OrgaTeamPermissionMixin, ListView):
    template_name = "orders_village.html"

    def get_queryset(self, **kwargs):
        camp_prefix = "BornHack {}".format(timezone.now().year)

        return (
            OrderProductRelation.objects.filter(
                ticket_generated=False,
                order__paid=True,
                order__refunded=False,
                order__cancelled=False,
                product__category__name="Villages",
            )
            .filter(product__name__startswith=camp_prefix)
            .order_by("order")
        )


class VillageToOrderView(CampViewMixin, OrgaTeamPermissionMixin, TemplateView):
    template_name = "village_to_order.html"

    def get_context_data(self, **kwargs):
        camp_prefix = "BornHack {}".format(timezone.now().year)

        order_relations = OrderProductRelation.objects.filter(
            ticket_generated=False,
            order__paid=True,
            order__refunded=False,
            order__cancelled=False,
            product__category__name="Villages",
        ).filter(product__name__startswith=camp_prefix)

        village_orders = {}
        for relation in order_relations:
            try:
                quantity = village_orders[relation.product.name] + relation.quantity
                village_orders[relation.product.name] = quantity
            except KeyError:
                village_orders[relation.product.name] = relation.quantity

        context = super().get_context_data(**kwargs)
        context["village"] = village_orders
        return context


################################
# CHAINS & CREDEBTORS


class ChainListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Chain
    template_name = "chain_list_backoffice.html"


class ChainDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Chain
    template_name = "chain_detail_backoffice.html"
    slug_url_kwarg = "chain_slug"


class CredebtorDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Credebtor
    template_name = "credebtor_detail_backoffice.html"
    slug_url_kwarg = "credebtor_slug"


################################
# EXPENSES


class ExpenseListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Expense
    template_name = "expense_list_backoffice.html"

    def get_queryset(self, **kwargs):
        """
        Exclude unapproved expenses, they are shown seperately
        """
        queryset = super().get_queryset(**kwargs)
        return queryset.exclude(approved__isnull=True)

    def get_context_data(self, **kwargs):
        """
        Include unapproved expenses seperately
        """
        context = super().get_context_data(**kwargs)
        context["unapproved_expenses"] = Expense.objects.filter(
            camp=self.camp, approved__isnull=True
        )
        return context


class ExpenseDetailView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Expense
    template_name = "expense_detail_backoffice.html"
    fields = ["notes"]

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        expense = form.save()
        if "approve" in form.data:
            # approve button was pressed
            expense.approve(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            expense.reject(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse("backoffice:expense_list", kwargs={"camp_slug": self.camp.slug})
        )


######################################
# REIMBURSEMENTS


class ReimbursementListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Reimbursement
    template_name = "reimbursement_list_backoffice.html"


class ReimbursementDetailView(CampViewMixin, EconomyTeamPermissionMixin, DetailView):
    model = Reimbursement
    template_name = "reimbursement_detail_backoffice.html"


class ReimbursementCreateUserSelectView(
    CampViewMixin, EconomyTeamPermissionMixin, ListView
):
    template_name = "reimbursement_create_userselect.html"

    def get_queryset(self):
        queryset = User.objects.filter(
            id__in=Expense.objects.filter(
                camp=self.camp,
                reimbursement__isnull=True,
                paid_by_bornhack=False,
                approved=True,
            )
            .values_list("user", flat=True)
            .distinct()
        )
        return queryset


class ReimbursementCreateView(CampViewMixin, EconomyTeamPermissionMixin, CreateView):
    model = Reimbursement
    template_name = "reimbursement_create.html"
    fields = ["notes", "paid"]

    def dispatch(self, request, *args, **kwargs):
        """ Get the user from kwargs """
        self.reimbursement_user = get_object_or_404(User, pk=kwargs["user_id"])

        # get response now so we have self.camp available below
        response = super().dispatch(request, *args, **kwargs)

        # return the response
        return response

    def get(self, request, *args, **kwargs):
        # does this user have any approved and un-reimbursed expenses?
        if not self.reimbursement_user.expenses.filter(
            reimbursement__isnull=True, approved=True, paid_by_bornhack=False
        ):
            messages.error(
                request, "This user has no approved and unreimbursed expenses!"
            )
            return redirect(
                reverse("backoffice:index", kwargs={"camp_slug": self.camp.slug})
            )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expenses"] = Expense.objects.filter(
            user=self.reimbursement_user,
            approved=True,
            reimbursement__isnull=True,
            paid_by_bornhack=False,
        )
        context["total_amount"] = context["expenses"].aggregate(Sum("amount"))
        context["reimbursement_user"] = self.reimbursement_user
        return context

    def form_valid(self, form):
        """
        Set user and camp for the Reimbursement before saving
        """
        # get the expenses for this user
        expenses = Expense.objects.filter(
            user=self.reimbursement_user,
            approved=True,
            reimbursement__isnull=True,
            paid_by_bornhack=False,
        )
        if not expenses:
            messages.error(self.request, "No expenses found")
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )

        # get the Economy team for this camp
        try:
            economyteam = Team.objects.get(
                camp=self.camp, name=settings.ECONOMYTEAM_NAME
            )
        except Team.DoesNotExist:
            messages.error(self.request, "No economy team found")
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )

        # create reimbursement in database
        reimbursement = form.save(commit=False)
        reimbursement.reimbursement_user = self.reimbursement_user
        reimbursement.user = self.request.user
        reimbursement.camp = self.camp
        reimbursement.save()

        # add all expenses to reimbursement
        for expense in expenses:
            expense.reimbursement = reimbursement
            expense.save()

        # create expense for this reimbursement
        expense = Expense()
        expense.camp = self.camp
        expense.user = self.request.user
        expense.amount = reimbursement.amount
        expense.description = "Payment of reimbursement %s to %s" % (
            reimbursement.pk,
            reimbursement.reimbursement_user,
        )
        expense.paid_by_bornhack = True
        expense.responsible_team = economyteam
        expense.approved = True
        expense.reimbursement = reimbursement
        expense.invoice_date = timezone.now()
        expense.creditor = Credebtor.objects.get(name="Reimbursement")
        expense.invoice.save(
            "na.jpg",
            File(
                open(
                    os.path.join(settings.DJANGO_BASE_PATH, "static_src/img/na.jpg"),
                    "rb",
                )
            ),
        )
        expense.save()

        messages.success(
            self.request,
            "Reimbursement %s has been created with invoice_date %s"
            % (reimbursement.pk, timezone.now()),
        )
        return redirect(
            reverse(
                "backoffice:reimbursement_detail",
                kwargs={"camp_slug": self.camp.slug, "pk": reimbursement.pk},
            )
        )


class ReimbursementUpdateView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Reimbursement
    template_name = "reimbursement_form.html"
    fields = ["notes", "paid"]

    def get_success_url(self):
        return reverse(
            "backoffice:reimbursement_detail",
            kwargs={"camp_slug": self.camp.slug, "pk": self.get_object().pk},
        )


class ReimbursementDeleteView(CampViewMixin, EconomyTeamPermissionMixin, DeleteView):
    model = Reimbursement
    template_name = "reimbursement_delete.html"
    fields = ["notes", "paid"]

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if self.get_object().paid:
            messages.error(
                request,
                "This reimbursement has already been paid so it cannot be deleted",
            )
            return redirect(
                reverse(
                    "backoffice:reimbursement_list",
                    kwargs={"camp_slug": self.camp.slug},
                )
            )
        return response


################################
# REVENUES


class RevenueListView(CampViewMixin, EconomyTeamPermissionMixin, ListView):
    model = Revenue
    template_name = "revenue_list_backoffice.html"

    def get_queryset(self, **kwargs):
        """
        Exclude unapproved revenues, they are shown seperately
        """
        queryset = super().get_queryset(**kwargs)
        return queryset.exclude(approved__isnull=True)

    def get_context_data(self, **kwargs):
        """
        Include unapproved revenues seperately
        """
        context = super().get_context_data(**kwargs)
        context["unapproved_revenues"] = Revenue.objects.filter(
            camp=self.camp, approved__isnull=True
        )
        return context


class RevenueDetailView(CampViewMixin, EconomyTeamPermissionMixin, UpdateView):
    model = Revenue
    template_name = "revenue_detail_backoffice.html"
    fields = ["notes"]

    def form_valid(self, form):
        """
        We have two submit buttons in this form, Approve and Reject
        """
        revenue = form.save()
        if "approve" in form.data:
            # approve button was pressed
            revenue.approve(self.request)
        elif "reject" in form.data:
            # reject button was pressed
            revenue.reject(self.request)
        else:
            messages.error(self.request, "Unknown submit action")
        return redirect(
            reverse("backoffice:revenue_list", kwargs={"camp_slug": self.camp.slug})
        )


def _ticket_getter_by_token(token):
    for ticket_class in [ShopTicket, SponsorTicket, DiscountTicket]:
        try:
            return ticket_class.objects.get(token=token), False
        except ticket_class.DoesNotExist:
            try:
                return ticket_class.objects.get(badge_token=token), True
            except ticket_class.DoesNotExist:
                pass


def _ticket_getter_by_pk(pk):
    for ticket_class in [ShopTicket, SponsorTicket, DiscountTicket]:
        try:
            return ticket_class.objects.get(pk=pk)
        except ticket_class.DoesNotExist:
            pass


class ScanTicketsView(
    LoginRequiredMixin, InfoTeamPermissionMixin, CampViewMixin, TemplateView
):
    template_name = "info_desk/scan.html"

    ticket = None
    order = None
    order_search = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.ticket:
            context["ticket"] = self.ticket

        elif "ticket_token" in self.request.POST:

            # Slice to get rid of the first character which is a '#'
            ticket_token = self.request.POST.get("ticket_token")[1:]

            ticket, is_badge = _ticket_getter_by_token(ticket_token)

            if ticket:
                context["ticket"] = ticket
                context["is_badge"] = is_badge
            else:
                messages.warning(self.request, "Ticket not found!")

        elif self.order_search:
            context["order"] = self.order

        return context

    def post(self, request, **kwargs):
        if "check_in_ticket_id" in request.POST:
            self.ticket = self.check_in_ticket(request)
        elif "badge_ticket_id" in request.POST:
            self.ticket = self.hand_out_badge(request)
        elif "find_order_id" in request.POST:
            self.order_search = True
            try:
                order_id = self.request.POST.get("find_order_id")
                self.order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                pass
        elif "mark_as_paid" in request.POST:
            self.mark_order_as_paid(request)

        return super().get(request, **kwargs)

    def check_in_ticket(self, request):
        check_in_ticket_id = request.POST.get("check_in_ticket_id")
        ticket_to_check_in = _ticket_getter_by_pk(check_in_ticket_id)
        ticket_to_check_in.used = True
        ticket_to_check_in.save()
        messages.info(request, "Ticket checked-in!")
        return ticket_to_check_in

    def hand_out_badge(self, request):
        badge_ticket_id = request.POST.get("badge_ticket_id")
        ticket_to_handout_badge_for = _ticket_getter_by_pk(badge_ticket_id)
        ticket_to_handout_badge_for.badge_handed_out = True
        ticket_to_handout_badge_for.save()
        messages.info(request, "Badge marked as handed out!")
        return ticket_to_handout_badge_for

    def mark_order_as_paid(self, request):
        order = Order.objects.get(id=request.POST.get("mark_as_paid"))
        order.mark_as_paid()
        messages.success(request, "Order #{} has been marked as paid!".format(order.id))


class ShopTicketOverview(LoginRequiredMixin, CampViewMixin, ListView):

    model = ShopTicket

    template_name = "shop_ticket_overview.html"

    context_object_name = "shop_tickets"

    def get_context_data(self, *, object_list=None, **kwargs):
        kwargs["ticket_types"] = TicketType.objects.filter(camp=self.camp)
        return super().get_context_data(object_list=object_list, **kwargs)


class BackofficeProxyView(CampViewMixin, RaisePermissionRequiredMixin, FormView):
    """
    Show proxied stuff, only for simple HTML pages with no external content
    Define URLs in settings.BACKOFFICE_PROXY_URLS as a dict of description: url pairs
    """

    permission_required = "camps.backoffice_permission"
    template_name = "backoffice_proxy.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.form_class = forms.Form

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.fields["url"] = forms.ChoiceField(
            choices=[
                (url, desc) for desc, url in settings.BACKOFFICE_PROXY_URLS.items()
            ],
            widget=forms.RadioSelect,
            help_text="Pick the URL you wish to see",
        )
        return form

    def form_valid(self, form):
        """ Perform the request and return the response """
        if form.cleaned_data["url"] not in settings.BACKOFFICE_PROXY_URLS.values():
            # this is not one of the urls from settings
            messages.error(self.request, "Unknown URL")
            return redirect(
                reverse("backoffice:proxy", kwargs={"camp_slug": self.camp.slug})
            )
        # perform the request
        r = requests.get(form.cleaned_data["url"])
        # return the response, keeping the status code but no headers
        return HttpResponse(r.content, status=r.status_code)
