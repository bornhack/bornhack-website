from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from shop.pdf import generate_pdf_letter
from shop.email import send_invoice_email
from shop.models import Order, Invoice
from time import sleep


class Command(BaseCommand):
    args = 'none'
    help = 'Send out invoices that have not been sent yet'

    def handle(self, *args, **options):
        self.stdout.write('Invoice worker running...')
        while True:
            # check if we need to generate any invoices
            for order in Order.objects.filter(paid=True, invoice__isnull=True):
                # generate invoice for this Order
                Invoice.objects.create(order=order)
                self.stdout.write('Generated Invoice object for order %s' % order)

            # check if we need to generate any pdf invoices
            for invoice in Invoice.objects.filter(pdf__isnull=True):
                # put the dict with data for the pdf together
                formatdict = {
                    'invoice': invoice,
                }

                # generate the pdf
                try:
                    pdffile = generate_pdf_letter(
                        filename=invoice.filename,
                        template='invoice.html',
                        formatdict=formatdict,
                    )
                    self.stdout.write('Generated pdf for invoice %s' % invoice)
                except Exception as E:
                    self.stdout.write('ERROR: Unable to generate PDF file for invoice #%s. Error: %s' % (invoice.pk, E))
                    continue

                # so, do we have a pdf?
                if not pdffile:
                    self.stdout.write('ERROR: Unable to generate PDF file for invoice #%s' % invoice.pk)
                    continue

                # update invoice object with the file
                invoice.pdf.save(invoice.filename, File(pdffile))
                invoice.save()

            # check if we need to send out any invoices (only where pdf has been generated)
            for invoice in Invoice.objects.filter(sent_to_customer=False).exclude(pdf=''):
                # send the email
                if send_invoice_email(invoice=invoice):
                    self.stdout.write('OK: Invoice email sent to %s' % invoice.order.user.email)
                    invoice.sent_to_customer=True
                    invoice.save()
                else:
                    self.stdout.write('ERROR: Unable to send invoice email for order %s to %s' % (invoice.order.pk, invoice.order.user.email))

            # pause for a bit
            sleep(60)

