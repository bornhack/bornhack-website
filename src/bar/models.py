from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel


class ProductCategory(ExportModelOperationsMixin("product_category"), CampRelatedModel):
    name = models.CharField(max_length=255)
    camp = models.ForeignKey("camps.Camp", on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class Product(ExportModelOperationsMixin("product"), models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    category = models.ForeignKey(
        ProductCategory,
        related_name="products",
        on_delete=models.PROTECT,
    )
    in_stock = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
