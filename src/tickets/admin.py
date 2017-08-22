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
    list_display = [
        'name',
        'camp',
    ]

    list_filter = [
        'name',
        'camp',
    ]


@admin.register(SponsorTicket)
class SponsorTicketAdmin(BaseTicketAdmin):
    list_display = [
        'pk',
        'ticket_type',
        'sponsor',
        'checked_in',
    ]

    list_filter = [
        'checked_in',
        'ticket_type',
        'sponsor',
    ]

    search_fields = ['name', 'email', 'sponsor__name']


@admin.register(DiscountTicket)
class DiscountTicketAdmin(BaseTicketAdmin):
    pass


@admin.register(ShopTicket)
class ShopTicketAdmin(BaseTicketAdmin):
    list_display = [
        'pk',
        'ticket_type',
        'order',
        'product',
        'checked_in',
    ]

    list_filter = [
        'ticket_type__camp',
        'checked_in',
        'ticket_type',
        'order',
        'product',
    ]

    search_fields = ['order__id', 'name', 'email']
