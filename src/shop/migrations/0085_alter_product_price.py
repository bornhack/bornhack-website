# Generated by Django 4.2.16 on 2024-10-06 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0084_subproductrelation_product_sub_products'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.IntegerField(help_text='Price of the product (in DKK, including VAT). The price can not be changed.'),
        ),
    ]