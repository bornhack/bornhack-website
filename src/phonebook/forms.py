"""Forms for the phonebook."""

from __future__ import annotations

import re
from typing import ClassVar

from django import forms

from .dectutils import DectUtils
from .exceptions import InvalidIPEIError
from .models import DectRegistration

dectutil = DectUtils()


class DectRegistrationForm(forms.ModelForm):
    """Dect Registration Form used in the phonebook registration create view."""

    ipei_help_text = """
    Optional: Enter your IPEI (03562 0900847) or IPUI (00DEADBEEF)<br>
    Entering this will enable you to register your handset directly when you arrive<br>
    You can find your IPUI on most Siemens handsets by going to menu and dailing *#06#
    """
    ipei = forms.CharField(
        max_length=13,
        help_text=ipei_help_text,
        required=False,
        label="IPEI/IPUI",
    )

    class Meta:
        """Meta info of class."""

        model = DectRegistration
        fields: ClassVar[list[str]] = ["number", "letters", "description", "publish_in_phonebook", "ipei"]

    def clean_ipei(self) -> None | list[int]:
        """Detect IPEI type and convert both IPEI or IPUI to a array of ints."""
        ipei_s = self.cleaned_data["ipei"]
        if len(ipei_s) == 10:  # noqa: PLR2004
            ipei = dectutil.hex_ipui_ipei(ipei_s)
        elif len(ipei_s) == 13:  # noqa: PLR2004
            if re.match(r"^\d{5} \d{7}$", ipei_s):
                ipei = [int(a) for a in ipei_s.split(" ")]
            else:
                raise InvalidIPEIError(ipei=[])
        elif ipei_s == "":
            return None
        else:
            raise InvalidIPEIError(ipei=[])

        if not ipei:
            raise InvalidIPEIError(ipei=ipei)
        return ipei

    def clean(self) -> dict:
        """Clean data."""
        cleaned_data = super().clean()
        ipei = cleaned_data.get("ipei")

        if ipei and len(ipei) != 2:  # noqa: PLR2004
            self.add_error("ipei", f"The ipei is incorrect. {ipei}")
        return cleaned_data
