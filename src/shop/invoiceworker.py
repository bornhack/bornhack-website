from django.core.files import File
from django.conf import settings
from django.utils import timezone
from shop.pdf import generate_pdf_letter
from shop.email import send_invoice_email, send_creditnote_email
from shop.models import Order, CustomOrder, Invoice, CreditNote
from decimal import Decimal
import logging


def run_invoice_worker():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # check if we need to generate any invoices for shop orders
    for order in Order.objects.filter(paid=True, invoice__isnull=True):
        # generate invoice for this Order
        Invoice.objects.create(order=order)
        logger.info('Generated Invoice object for %s' % order)

    # check if we need to generate any invoices for custom orders
    for customorder in CustomOrder.objects.filter(invoice__isnull=True):
        # generate invoice for this CustomOrder
        Invoice.objects.create(customorder=customorder)
        logger.info('Generated Invoice object for %s' % customorder)

    # check if we need to generate any pdf invoices
    for invoice in Invoice.objects.filter(pdf=''):
        # put the dict with data for the pdf together
        formatdict = {
            'invoice': invoice,
        }

        # generate the pdf
        try:
            if invoice.customorder:
                template='pdf/custominvoice.html'
            else:
                template='pdf/invoice.html'
            pdffile = generate_pdf_letter(
                filename=invoice.filename,
                template=template,
                formatdict=formatdict,
            )
            logger.info('Generated pdf for invoice %s' % invoice)
        except Exception as E:
            logger.error('ERROR: Unable to generate PDF file for invoice #%s. Error: %s' % (invoice.pk, E))
            continue

        # so, do we have a pdf?
        if not pdffile:
            logger.error('ERROR: Unable to generate PDF file for invoice #%s' % invoice.pk)
            continue

        # update invoice object with the file
        invoice.pdf.save(invoice.filename, File(pdffile))
        invoice.save()

    ###############################################################
    # check if we need to send out any invoices (only for shop orders, and only where pdf has been generated)
    for invoice in Invoice.objects.filter(order__isnull=False, sent_to_customer=False).exclude(pdf=''):
        # send the email
        if send_invoice_email(invoice=invoice):
            logger.info('OK: Invoice email sent to %s' % invoice.order.user.email)

