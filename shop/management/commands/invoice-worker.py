from django.core.management.base import BaseCommand
from shop.pdf import generate_pdf_letter
from shop.email import send_invoice_email


class Command(BaseCommand):
    args = 'none'
    help = 'Send out invoices that has not been sent yet'

    def handle(self, *args, **options):
        self.stdout.write('Invoice worker running...')
        while True:
            ### check if we need to generate any invoices
            for order in Order.objects.filter(paid=True, invoice__isnull=True):
                ### generate invoice for this Order
                Invoice.objects.create(order=order)

            ### check if we need to send out any invoices
            for invoice in Invoice.objects.filter(sent_to_customer=False):
                ### generate PDF invoice
                try:
                    pdffile = generate_pdf_letter('invoice.html', formatdict)
                except Exception as E:
                    self.stdout.write('ERROR: Unable to generate PDF file. Error: %s' % E)
                    continue
                if not pdffile:
                    self.stdout.write('ERROR: Unable to generate PDF file')
                    continue

                if send_invoice_email(recipient=invoice.order.user.email, invoice=invoice, attachment=pdffile):
                    self.stdout.write('OK: Invoice email sent to %s' % order.user.email)
                    invoice.sent_to_customer=True
                    invoice.save()
                else:
                    self.stdout.write('ERROR: Unable to send invoice email to %s' % order.user.email)

            ### pause for a bit
            sleep(60)


