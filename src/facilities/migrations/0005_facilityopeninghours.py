# Generated by Django 3.0.3 on 2020-06-06 12:06

import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("facilities", "0004_facilitytype_marker"),
    ]

    operations = [
        migrations.CreateModel(
            name="FacilityOpeningHours",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "when",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(
                        db_index=True,
                        help_text="The period when this facility is open.",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        help_text="Any notes for this period like 'no hot food after 20' or 'no alcohol sale after 02'. Optional.",
                    ),
                ),
                (
                    "facility",
                    models.ForeignKey(
                        help_text="The Facility to which these opening hours belong.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="opening_hours",
                        to="facilities.Facility",
                    ),
                ),
            ],
            options={"abstract": False,},
        ),
    ]