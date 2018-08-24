from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView

from camps.mixins import CampViewMixin
from .models import Reimbursement


class ReimbursementCreate(CampViewMixin, CreateView):
    model = Reimbursement

    def form_valid(self, form):
        reimbursement = form.save(commit=False)
        reimbursement.user = self.request.user
        reimbursement.camp = self.camp
        reimbursement.save()

        messages.success(
            self.request,
            "Your reimbursement has now been created. You will receive an email when it has been approved."
        )
        return HttpResponseRedirect(reverse('reimbursement', kwargs={'camp_slug': self.camp.slug}))
