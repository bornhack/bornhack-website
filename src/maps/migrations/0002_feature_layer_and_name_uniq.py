# Generated by Django 4.2.16 on 2024-09-25 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='feature',
            constraint=models.UniqueConstraint(fields=('layer', 'name'), name='layer_and_name_uniq'),
        ),
    ]
