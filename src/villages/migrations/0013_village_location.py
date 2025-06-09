from __future__ import annotations

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("villages", "0012_village_approved"),
    ]

    operations = [
        migrations.AddField(
            model_name="village",
            name="location",
            field=django.contrib.gis.db.models.fields.PointField(
                help_text="The location of this village",
                null=True,
                srid=4326,
            ),
        ),
    ]
