from django.contrib import admin

from reimbursement.models import Reimbursement


def approve_reimbursements(modeladmin, request, queryset):
    for reimbursement in queryset.all():
        reimbursement.approve()
approve_reimbursements.short_description = "Approve"


def reject_reimbursements(modeladmin, request, queryset):
    for reimbursement in queryset.all():
        reimbursement.reject()
reject_reimbursements.short_description = "Reject"


@admin.register(Reimbursement)
class ReimbursementAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'description', 'camp']
    list_filter = ['camp', 'approved']
    actions = [approve_reimbursements, reject_reimbursements]
