from django.contrib import admin

from .models import OutgoingEmail


class OutgoingEmailAdmin(admin.ModelAdmin):
    model = OutgoingEmail
    fields = ['subject', 'to_recipients']