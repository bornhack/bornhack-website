from __future__ import annotations

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from camps.models import Camp
from tickets.models import TicketType
from shop.models import Product, SubProductRelation

logger = logging.getLogger(f"bornhack.{__name__}")


class Command(BaseCommand):
    args = "none"
    help = "Create webshop tickets based on a different camp"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "from-camp-slug",
            help="The slug of the camp to copy tickets from, like bornhack-2016",
        )
        parser.add_argument(
            "to-camp-slug",
            help="The slug of the camp to copy tickets to, like bornhack-2017",
        )

    def output(self, message) -> None:
        self.stdout.write(
            "{}: {}".format(timezone.now().strftime("%Y-%m-%d %H:%M:%S"), message),
        )

    def handle(self, *args, **options) -> None:
        fromcamp = Camp.objects.get(slug=options["from-camp-slug"])
        tocamp = Camp.objects.get(slug=options["to-camp-slug"])
        self.output(
            self.style.SUCCESS(
                f"----------[ Copying tickets from {fromcamp.title} to {tocamp.title} ]----------",
            ),
        )
        # loop tickettypes to create regular products without subproducts
        products: dict[Product, Product] = {}
        for tt in TicketType.objects.filter(camp=fromcamp):
            newtt, created = TicketType.objects.get_or_create(
                name=tt.name,
                camp=tocamp,
                defaults={
                    "includes_badge": tt.includes_badge,
                    "single_ticket_per_product": tt.single_ticket_per_product,
                },
            )
            if created:
                print(f"Created new TicketType {newtt}")
            for product in tt.product_set.filter(sub_products__isnull=True):
                newprod, created = Product.objects.get_or_create(
                    name=product.name.replace(str(fromcamp.camp.lower.year), str(tocamp.camp.lower.year)),
                    ticket_type=newtt,
                    slug=product.slug.replace(str(fromcamp.camp.lower.year), str(tocamp.camp.lower.year)),
                    defaults={
                        "price": product.price,
                        "category": product.category,
                        "description": product.description.replace(str(fromcamp.camp.lower.year), str(tocamp.camp.lower.year)),
                        "available_in": (timezone.now(), tocamp.camp.upper + timedelta(days=30)),
                        "cost": product.cost,
                        "comment": product.comment.replace(str(fromcamp.camp.lower.year), str(tocamp.camp.lower.year)),
                    }
                )
                if created:
                    print(f"Created new product {newprod}")
                products[product] = newprod

        # loop again and create bundle products
        for product in Product.objects.filter(sub_products__isnull=False, sub_products__ticket_type__camp=fromcamp).distinct():
            print(product)
            # create bundle product
            newprod, created = Product.objects.get_or_create(
                name=product.name.replace(str(fromcamp.camp.lower.year), str(tocamp.camp.lower.year)),
                slug=product.slug.replace(str(fromcamp.camp.lower.year), str(tocamp.camp.lower.year)),
                defaults={
                    "price": product.price,
                    "category": product.category,
                    "description": product.description.replace(str(fromcamp.camp.lower.year), str(tocamp.camp.lower.year)),
                    "available_in": (timezone.now(), tocamp.camp.upper + timedelta(days=30)),
                    "cost": product.cost,
                    "comment": product.comment.replace(str(fromcamp.camp.lower.year), str(tocamp.camp.lower.year)),
                }
            )
            for spr in product.sub_product_relations.all():
                newspr, created = SubProductRelation.objects.get_or_create(
                    bundle_product=newprod,
                    sub_product=products[spr.sub_product],
                    number_of_tickets=spr.number_of_tickets,
                )
                if created:
                    print(f"Created new SPR {newspr} for bundle product {newprod}")
        self.output(
            self.style.SUCCESS(
                f"----------[ Done creating tickets! Remember to manually set FKs from camp to ticket types! ]----------",
            ),
        )
