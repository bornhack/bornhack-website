from django.contrib import admin

from reimbursement.models import Reimbursement


@admin.register(Reimbursement)
class ReimbursementAdmin(admin.ModelAdmin):
    pass
