from __future__ import annotations

import io
import logging
import os

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from django_weasyprint.utils import django_url_fetcher
from weasyprint import HTML

logger = logging.getLogger(f"bornhack.{__name__}")


def generate_pdf_letter(filename, template, formatdict):
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    request.session = {}
    formatdict["dev"] = settings.PDF_TEST_MODE
    weasy_html = HTML(
        string=render_to_string(template, context=formatdict, request=request),
        url_fetcher=django_url_fetcher,
        base_url="file://",
    )
    pdf = io.BytesIO()
    pdf.write(weasy_html.write_pdf())
    weasy_html.write_pdf(os.path.join(settings.PDF_ARCHIVE_PATH, filename))
    return pdf
