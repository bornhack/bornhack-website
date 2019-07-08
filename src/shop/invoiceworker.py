from django.conf import settings
from django.core.files import File
from utils.pdf import generate_pdf_letter
from shop.email import add_invoice_email, add_creditnote_email
from shop.models import Order, CustomOrder, Invoice, CreditNote
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bornhack.%s" % __name__)


def do_work():
    """
        The invoice worker creates Invoice objects for shop orders and
        for custom orders. It also generates PDF files for Invoice objects
        that have no PDF. It also emails invoices for shop orders.
    """

    # check if we need to generate any invoices for shop orders
    for order in Order.objects.filter(paid=True, invoice__isnull=True):
        # generate invoice for this Order
        Invoice.objects.create(order=order)
        logger.info("Generated Invoice object for %s" % order)

    # check if we need to generate any invoices for custom orders
    for customorder in CustomOrder.objects.filter(invoice__isnull=True):
        # generate invoice for this CustomOrder
        Invoice.objects.create(customorder=customorder)
        logger.info("Generated Invoice object for %s" % customorder)

    # check if we need to generate any pdf invoices
    for invoice in Invoice.objects.filter(pdf=""):
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
                "Unable to generate PDF file for invoice #%s. Error: %s"
                % (invoice.pk, E)
            )
            continue

        # update invoice object with the file
        invoice.pdf.save(invoice.filename, File(pdffile))
        invoice.save()

    # check if we need to send out any invoices (only for shop orders, and only where pdf has been generated)
    for invoice in Invoice.objects.filter(
        order__isnull=False, sent_to_customer=False
    ).exclude(pdf=""):
        logger.info("found unmailed Invoice object: %s" % invoice)
        # add email to the outgoing email queue
        if add_invoice_email(invoice=invoice):
            invoice.sent_to_customer = True
            invoice.save()
            logger.info(
                "OK: Invoice email to {} added to queue.".format(
                    invoice.order.user.email
                )
            )
        else:
            logger.error(
                "Unable to add email for invoice {} to {}".format(
                    invoice.pk, invoice.order.user.email
                )
            )

    # check if we need to generate any pdf creditnotes?
    for creditnote in CreditNote.objects.filter(pdf=""):
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
                "Unable to generate PDF file for creditnote #%s. Error: %s"
                % (creditnote.pk, E)
            )
            continue

        # update creditnote object with the file
        creditnote.pdf.save(creditnote.filename, File(pdffile))
        creditnote.save()

    # check if we need to send out any creditnotes (only where pdf has been generated and only for creditnotes linked to a user)
    for creditnote in (
        CreditNote.objects.filter(sent_to_customer=False)
        .exclude(pdf="")
        .exclude(user=None)
    ):
        # send the email
        if add_creditnote_email(creditnote=creditnote):
            logger.info("OK: Creditnote email to %s added" % creditnote.user.email)
            creditnote.sent_to_customer = True
            creditnote.save()
        else:
            logger.error(
                "Unable to add creditnote email for creditnote %s to %s"
                % (creditnote.pk, creditnote.user.email)
            )
