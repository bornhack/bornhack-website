from django.contrib import admin

from .models import OutgoingEmail


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(admin.ModelAdmin):
    pass
