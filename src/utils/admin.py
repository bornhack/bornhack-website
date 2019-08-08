from django.contrib import admin

from .models import OutgoingEmail


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(admin.ModelAdmin):
    model = OutgoingEmail
    fields = ['subject', 'to_recipients']
