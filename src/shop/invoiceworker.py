from __future__ import annotations

import logging

from django.conf import settings
from django.core.files import File
from django.db.models import Q

from shop.email import add_creditnote_email
from shop.email import add_invoice_email
from shop.models import CreditNote
from shop.models import CustomOrder
from shop.models import Invoice
from shop.models import Order
from shop.models import Refund
from utils.pdf import generate_pdf_letter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bornhack.%s" % __name__)


def do_work():
    """The invoice worker creates Invoice objects for shop orders and
    for custom orders. It also generates PDF files for Invoice objects
    that have no PDF. It also emails invoices for shop orders.
    It also generates proforma invoices for all closed orders.
    """
    # check if we need to generate any proforma invoices for shop orders
    for order in Order.objects.filter(
        Q(pdf="") | Q(pdf__isnull=True),
        open__isnull=True,
    ):
        # generate proforma invoice for this Order
        pdffile = generate_pdf_letter(
            filename=order.filename,
            template="pdf/proforma_invoice.html",
            formatdict={
                "hostname": settings.ALLOWED_HOSTS[0],
                "order": order,
                "bank": settings.BANKACCOUNT_BANK,
                "bank_iban": settings.BANKACCOUNT_IBAN,
                "bank_bic": settings.BANKACCOUNT_SWIFTBIC,
                "bank_dk_reg": settings.BANKACCOUNT_REG,
                "bank_dk_accno": settings.BANKACCOUNT_ACCOUNT,
            },
        )
        # update order object with the file
        order.pdf.save(str(order.filename), File(pdffile))
        order.save()
        logger.info(f"Generated proforma invoice PDF for order {order}")

    # check if we need to generate any invoices for shop orders
    for order in Order.objects.filter(paid=True, invoice__isnull=True):
        # generate invoice for this Order
        Invoice.objects.create(order=order)
        logger.info(f"Generated Invoice object for {order}")

    # check if we need to generate any invoices for custom orders
    for customorder in CustomOrder.objects.filter(invoice__isnull=True):
        # generate invoice for this CustomOrder
        Invoice.objects.create(customorder=customorder)
        logger.info(f"Generated Invoice object for {customorder}")

    # check if we need to generate any creditnotes for refunds
    for refund in Refund.objects.filter(paid=True, creditnote__isnull=True):
        # generate CreditNote for this Refund
        CreditNote.objects.create(
            refund=refund,
            invoice=refund.order.invoice,
            amount=refund.amount,
            text=f"Refund for order #{refund.order.id}",
            user=refund.order.user,
        )
        logger.info(f"Generated CreditNote object for {refund}")

    # check if we need to generate any pdf invoices
    for invoice in Invoice.objects.filter(Q(pdf="") | Q(pdf__isnull=True)):
        # generate the pdf
        try:
            if invoice.customorder:
                template = "pdf/custominvoice.html"
            else:
                template = "pdf/invoice.html"
            pdffile = generate_pdf_letter(
                filename=invoice.filename,
                template=template,
                formatdict={
                    "invoice": invoice,
                    "bank": settings.BANKACCOUNT_BANK,
                    "bank_iban": settings.BANKACCOUNT_IBAN,
                    "bank_bic": settings.BANKACCOUNT_SWIFTBIC,
                    "bank_dk_reg": settings.BANKACCOUNT_REG,
                    "bank_dk_accno": settings.BANKACCOUNT_ACCOUNT,
                },
            )
            logger.info("Generated pdf for invoice %s" % invoice)
        except Exception as E:
            logger.exception(
                "Unable to generate PDF file for invoice #%s. Error: %s" % (invoice.pk, E),
            )
            continue

        # update invoice object with the file
        invoice.pdf.save(str(invoice.filename), File(pdffile))
        invoice.save()

    # check if we need to send out any invoices (only for shop orders, and only where pdf has been generated)
    for invoice in Invoice.objects.filter(
        order__isnull=False,
        sent_to_customer=False,
    ).exclude(pdf=""):
        logger.info("found unmailed Invoice object: %s" % invoice)
        # add email to the outgoing email queue
        if add_invoice_email(invoice=invoice):
            invoice.sent_to_customer = True
            invoice.save()
            logger.info(
                f"OK: Invoice email to {invoice.order.user.email} added to queue.",
            )
        else:
            logger.error(
                f"Unable to add email for invoice {invoice.pk} to {invoice.order.user.email}",
            )

    # check if we need to generate any pdf creditnotes?
    for creditnote in CreditNote.objects.filter(Q(pdf="") | Q(pdf__isnull=True)):
        # generate the pdf
        try:
            pdffile = generate_pdf_letter(
                filename=creditnote.filename,
                template="pdf/creditnote.html",
                formatdict={"creditnote": creditnote},
            )
            logger.info("Generated pdf for creditnote %s" % creditnote)
        except Exception as E:
            logger.exception(
                "Unable to generate PDF file for creditnote #%s. Error: %s" % (creditnote.pk, E),
            )
            continue

        # update creditnote object with the file
        creditnote.pdf.save(creditnote.filename, File(pdffile))
        creditnote.save()

    # check if we need to send out any creditnotes (only where pdf has been generated and only for creditnotes linked to a user)
    for creditnote in CreditNote.objects.filter(sent_to_customer=False).exclude(pdf="").exclude(user=None):
        # send the email
        if add_creditnote_email(creditnote=creditnote):
            logger.info("OK: Creditnote email to %s added" % creditnote.user.email)
            creditnote.sent_to_customer = True
            creditnote.save()
        else:
            logger.error(
                "Unable to add creditnote email for creditnote %s to %s" % (creditnote.pk, creditnote.user.email),
            )
