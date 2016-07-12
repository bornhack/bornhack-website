from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from django.utils import timezone
from shop.pdf import generate_pdf_letter
from shop.email import send_invoice_email, send_creditnote_email
from shop.models import Order, CustomOrder, Invoice, CreditNote
from time import sleep
from decimal import Decimal


class Command(BaseCommand):
    args = 'none'
    help = 'Generate invoices and credit notes, and email invoices that have not been sent yet'

    def output(self, message):
        self.stdout.write('%s: %s' % (timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message))

    def handle(self, *args, **options):
        self.output('Invoice worker running...')
        while True:
            # check if we need to generate any invoices for shop orders
            for order in Order.objects.filter(paid=True, invoice__isnull=True):
                # generate invoice for this Order
                Invoice.objects.create(order=order)
                self.output('Generated Invoice object for %s' % order)

            # check if we need to generate any invoices for custom orders
            for customorder in CustomOrder.objects.filter(invoice__isnull=True):
                # generate invoice for this CustomOrder
                Invoice.objects.create(customorder=customorder)
                self.output('Generated Invoice object for %s' % customorder)

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
                    self.output('Generated pdf for invoice %s' % invoice)
                except Exception as E:
                    self.output('ERROR: Unable to generate PDF file for invoice #%s. Error: %s' % (invoice.pk, E))
                    continue

                # so, do we have a pdf?
                if not pdffile:
                    self.output('ERROR: Unable to generate PDF file for invoice #%s' % invoice.pk)
                    continue

                # update invoice object with the file
                invoice.pdf.save(invoice.filename, File(pdffile))
                invoice.save()

            ###############################################################
            # check if we need to send out any invoices (only for shop orders, and only where pdf has been generated)
            for invoice in Invoice.objects.filter(order__isnull=False, sent_to_customer=False).exclude(pdf=''):
                # send the email
                if send_invoice_email(invoice=invoice):
                    self.output('OK: Invoice email sent to %s' % invoice.order.user.email)
                    invoice.sent_to_customer=True
                    invoice.save()
                else:
                    self.output('ERROR: Unable to send invoice email for order %s to %s' % (invoice.order.pk, invoice.order.user.email))

            ###############################################################
            # check if we need to generate any pdf creditnotes?
            for creditnote in CreditNote.objects.filter(pdf=''):
                # put the dict with data for the pdf together
                formatdict = {
                    'creditnote': creditnote,
                }

                # generate the pdf
                try:
                    pdffile = generate_pdf_letter(
                        filename=creditnote.filename,
                        template='pdf/creditnote.html',
                        formatdict=formatdict,
                    )
                    self.output('Generated pdf for creditnote %s' % creditnote)
                except Exception as E:
                    self.output('ERROR: Unable to generate PDF file for creditnote #%s. Error: %s' % (creditnote.pk, E))
                    continue

                # so, do we have a pdf?
                if not pdffile:
                    self.output('ERROR: Unable to generate PDF file for creditnote #%s' % creditnote.pk)
                    continue

                # update creditnote object with the file
                creditnote.pdf.save(creditnote.filename, File(pdffile))
                creditnote.save()

            ###############################################################
            # check if we need to send out any creditnotes (only where pdf has been generated)
            for creditnote in CreditNote.objects.filter(sent_to_customer=False).exclude(pdf=''):
                # send the email
                if send_creditnote_email(creditnote=creditnote):
                    self.output('OK: Creditnote email sent to %s' % creditnote.user.email)
                    creditnote.sent_to_customer=True
                    creditnote.save()
                else:
                    self.output('ERROR: Unable to send creditnote email for creditnote %s to %s' % (creditnote.pk, creditnote.user.email))

            # pause for a bit
            sleep(60)

