from django.db import models

from utils.models import CampRelatedModel


class ProductCategory(CampRelatedModel):
    name = models.CharField(max_length=255)
    camp = models.ForeignKey('camps.Camp')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    category = models.ForeignKey(ProductCategory, related_name="products")
    in_stock = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
