from django.contrib import admin

from .models import (
    TicketType,
    SponsorTicket,
    DiscountTicket,
    ShopTicket
)


class BaseTicketAdmin(admin.ModelAdmin):
    actions = ['generate_pdf']
    exclude = ['qrcode_base64']

    def generate_pdf(self, request, queryset):
        for ticket in queryset.all():
            ticket.generate_pdf()
    generate_pdf.description = 'Generate PDF for the ticket'


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(SponsorTicket)
class SponsorTicketAdmin(BaseTicketAdmin):
    pass


@admin.register(DiscountTicket)
class DiscountTicketAdmin(BaseTicketAdmin):
    pass


@admin.register(ShopTicket)
class ShopTicketAdmin(BaseTicketAdmin):
    pass
