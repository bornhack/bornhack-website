from django.contrib import admin

from .models import OutgoingEmail


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(admin.ModelAdmin):
    model = OutgoingEmail
    list_display = ["subject", "to_recipients", "processed", "hold", "responsible_team"]
    list_filter = ["processed", "hold", "responsible_team"]
