"""Functions used to bootstrap/test the application."""

from __future__ import annotations

import logging

import pytz
from faker import Faker

fake = Faker()
tz = pytz.timezone("Europe/Copenhagen")
logger = logging.getLogger(f"bornhack.{__name__}")


def output_fake_md_description() -> str:
    """Method for creating a fake markup description using Faker()."""
    fake_text = "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "\n\n"
    fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "\n\n"
    fake_text += "## " + fake.sentence(nb_words=3) + "\n"
    fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "\n\n"
    fake_text += '![The image is not awailable](/static/img/na.jpg "not available")'
    fake_text += "\n\n"
    fake_text += "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "\n\n"
    fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"
    fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"
    return fake_text


def output_fake_description() -> str:
    """Method for creating a fake description using Faker()."""
    fake_text = "\n".join(fake.paragraphs(nb=3, ext_word_list=None))
    fake_text += "* [" + fake.sentence(nb_words=3) + "](" + fake.uri() + ")\n"
    return fake_text
