from __future__ import annotations

from django.conf import settings
from django.views.generic import TemplateView


class ContactView(TemplateView):
    template_name = "contact.html"

    def get_context_data(self, **kwargs):
        return {
            "bank": settings.BANKACCOUNT_BANK,
            "bank_iban": settings.BANKACCOUNT_IBAN,
            "bank_bic": settings.BANKACCOUNT_SWIFTBIC,
            "bank_dk_reg": settings.BANKACCOUNT_REG,
            "bank_dk_accno": settings.BANKACCOUNT_ACCOUNT,
        }
