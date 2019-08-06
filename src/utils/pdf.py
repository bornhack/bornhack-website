import logging
import io
import os

from django.contrib.auth.models import AnonymousUser
from wkhtmltopdf.views import PDFTemplateResponse
from PyPDF2 import PdfFileWriter, PdfFileReader
from django.test.client import RequestFactory
from django.conf import settings

logger = logging.getLogger("bornhack.%s" % __name__)


def generate_pdf_letter(filename, template, formatdict):
    logger.debug(
        "Generating PDF with filename %s and template %s" % (filename, template)
    )

    # conjure up a fake request for PDFTemplateResponse
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    request.session = {}

    # produce text-only PDF from template
    pdfgenerator = PDFTemplateResponse(
        request=request,
        template=template,
        context=formatdict,
        cmd_options={"margin-top": 50, "margin-bottom": 50},
    )
    textonlypdf = io.BytesIO()
    textonlypdf.write(pdfgenerator.rendered_content)

    # create a blank pdf to work with
    finalpdf = PdfFileWriter()

    # open the text-only pdf
    pdfreader = PdfFileReader(textonlypdf)

    # get watermark from watermark file
    watermark = PdfFileReader(
        open(
            os.path.join(
                settings.STATICFILES_DIRS[0], "pdf", settings.PDF_LETTERHEAD_FILENAME
            ),
            "rb",
        )
    )

    # add the watermark to all pages
    for pagenum in range(pdfreader.getNumPages()):
        page = pdfreader.getPage(pagenum)
        try:
            page.mergePage(watermark.getPage(0))
        except ValueError:
            # watermark pdf might be broken?
            return False
        # add page to output
        finalpdf.addPage(page)

    # save the generated pdf to the archive
    fullpath = os.path.join(settings.PDF_ARCHIVE_PATH, filename)
    with open(fullpath, "wb") as fh:
        finalpdf.write(fh)
        logger.info("Saved pdf to archive: %s" % fullpath)

    returnfile = io.BytesIO()
    finalpdf.write(returnfile)
    return returnfile
