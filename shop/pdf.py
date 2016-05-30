from wkhtmltopdf.views import PDFTemplateResponse
from PyPDF2 import PdfFileWriter, PdfFileReader
from django.test.client import RequestFactory
from django.conf import settings
import StringIO

def generate_pdf_letter(filename, template, formatdict):
    ### produce text-only PDF from template
    pdfgenerator = PDFTemplateResponse(
        request=RequestFactory().get('/'), 
        template=template, 
        context=formatdict,
        cmd_options={
            'margin-top': 60,
            'margin-bottom': 50,
        },
    )
    textonlypdf = StringIO.StringIO()
    textonlypdf.write(pdfgenerator.rendered_content)

    ### create a blank pdf to work with
    finalpdf = PdfFileWriter()

    ### open the text-only pdf
    pdfreader = PdfFileReader(textonlypdf)

    ### get watermark from watermark file
    watermark = PdfFileReader(open(settings.LETTERHEAD_PDF_PATH, 'rb'))

    ### add the watermark to all pages
    for pagenum in xrange(pdfreader.getNumPages()):
        page = pdfreader.getPage(pagenum)
        try:
            page.mergePage(watermark.getPage(0))
        except ValueError:
            ### watermark pdf might be broken?
            return False
        ### add page to output
        finalpdf.addPage(page)

    ### save the generated pdf to the archive
    with open(settings.PDF_ARCHIVE_PATH+filename, 'wb') as fh:
        finalpdf.write(fh)
        print('Saved pdf to archive: %s' % settings.PDF_ARCHIVE_PATH+filename)

    ### return a file object with the data
    returnfile = StringIO.StringIO()
    finalpdf.write(returnfile)
    return returnfile

