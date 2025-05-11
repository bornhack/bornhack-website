from __future__ import annotations

from django.contrib import admin

from .models import OutgoingIrcMessage

admin.site.register(OutgoingIrcMessage)
