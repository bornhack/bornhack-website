from __future__ import annotations

from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import QuerySet
from django.utils import timezone


class ProductQuerySet(QuerySet):
    def available(self):
        return self.filter(available_in__contains=timezone.now(), category__public=True)

    def annotate_subproducts(self):
        from .models import SubProductRelation

        subproducts = SubProductRelation.objects.filter(
            bundle_product=OuterRef("pk"),
        )
        return self.annotate(
            has_subproducts=Exists(subproducts),
        )


class OrderQuerySet(QuerySet):
    def not_cancelled(self):
        return self.filter(cancelled=False)

    def open(self):
        return self.filter(open__isnull=False)

    def paid(self):
        return self.filter(paid=True)

    def unpaid(self):
        return self.filter(paid=False)

    def cancelled(self):
        return self.filter(cancelled=True)
