from __future__ import annotations

from django.contrib import admin

from .models import PrizeTicket
from .models import ShopTicket
from .models import SponsorTicket
from .models import TicketType


class BaseTicketAdmin(admin.ModelAdmin):
    actions = ["generate_pdf"]
    exclude = ["qrcode_base64"]
    readonly_fields = ["token", "badge_token"]

    def generate_pdf(self, request, queryset) -> None:
        for ticket in queryset.all():
            ticket.generate_pdf()

    generate_pdf.description = "Generate PDF for the ticket"


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "name",
        "camp",
        "includes_badge",
        "single_ticket_per_product",
    ]
    list_filter = ["name", "camp", "includes_badge", "single_ticket_per_product"]
    save_as = True


@admin.register(SponsorTicket)
class SponsorTicketAdmin(BaseTicketAdmin):
    list_display = ["pk", "ticket_type", "sponsor", "used_at"]

    list_filter = ["ticket_type__camp", "used_at", "ticket_type", "sponsor"]

    search_fields = ["pk", "sponsor__name"]


@admin.register(PrizeTicket)
class PrizeTicketAdmin(BaseTicketAdmin):
    pass


@admin.register(ShopTicket)
class ShopTicketAdmin(BaseTicketAdmin):
    def user_email(self, obj):
        return obj.order.user.email

    def is_paid(self, obj):
        return obj.order.paid

    list_display = [
        "pk",
        "user_email",
        "is_paid",
        "ticket_type",
        "order",
        "product",
        "used_at",
        "product_quantity",
    ]

    list_filter = [
        "ticket_type__camp",
        "used_at",
        "ticket_type",
        "opr__order",
        "product",
        "ticket_group",
    ]

    search_fields = [
        "uuid",
        "opr__order__id",
        "opr__order__user__email",
        "name",
        "email",
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "ticket_type",
                "ticket_type__camp",
                "product",
                "product__ticket_type__camp",
                "bundle_product",
            )
        )

    @admin.display(
        description="Quantity",
    )
    def product_quantity(self, ticket):
        return str(ticket.quantity)

    def generate_pdf(self, request, queryset) -> None:
        for ticket in queryset.all():
            ticket.generate_pdf()


class ShopTicketInline(admin.TabularInline):
    model = ShopTicket
