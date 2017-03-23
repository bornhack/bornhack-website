from wkhtmltopdf.views import PDFTemplateResponse
from PyPDF2 import PdfFileWriter, PdfFileReader
from django.test.client import RequestFactory
from django.conf import settings
import io
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def generate_pdf_letter(filename, template, formatdict):
    ### produce text-only PDF from template
    pdfgenerator = PDFTemplateResponse(
        request=RequestFactory().get('/'),
        template=template, 
        context=formatdict,
        cmd_options={
            'margin-top': 50,
            'margin-bottom': 50,
        },
    )
    textonlypdf = io.StringIO()
    textonlypdf.write(pdfgenerator.rendered_content)

    ### create a blank pdf to work with
    finalpdf = PdfFileWriter()

    ### open the text-only pdf
    pdfreader = PdfFileReader(textonlypdf)

    ### get watermark from watermark file
    watermark = PdfFileReader(open(settings.LETTERHEAD_PDF_PATH, 'rb'))

    ### add the watermark to all pages
    for pagenum in range(pdfreader.getNumPages()):
        page = watermark.getPage(0)
        try:
            page.mergePage(pdfreader.getPage(pagenum))
        except ValueError:
            ### watermark pdf might be broken?
            return False
        ### add page to output
        finalpdf.addPage(page)

    ### save the generated pdf to the archive
    with open(settings.PDF_ARCHIVE_PATH+filename, 'wb') as fh:
        finalpdf.write(fh)
        logger.info('Saved pdf to archive: %s' % settings.PDF_ARCHIVE_PATH+filename)

    ### return a file object with the data
    returnfile = io.StringIO()
    finalpdf.write(returnfile)
    return returnfile

