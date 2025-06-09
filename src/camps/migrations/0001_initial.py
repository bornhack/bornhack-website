from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.postgres.operations import BtreeGistExtension
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        BtreeGistExtension(),
        CreateExtension("postgis"),
        migrations.CreateModel(
            name="Camp",
            fields=[
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        serialize=False,
                        editable=False,
                        primary_key=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=255,
                        help_text="Name of the camp, ie. Bornhack.",
                        verbose_name="Name",
                    ),
                ),
                (
                    "start",
                    models.DateTimeField(
                        help_text="When the camp starts.",
                        unique=True,
                        verbose_name="Start date",
                    ),
                ),
                (
                    "end",
                    models.DateTimeField(
                        help_text="When the camp ends.",
                        unique=True,
                        verbose_name="End date",
                    ),
                ),
            ],
            options={"verbose_name_plural": "Camps", "verbose_name": "Camp"},
        ),
        migrations.CreateModel(
            name="Day",
            fields=[
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        serialize=False,
                        editable=False,
                        primary_key=True,
                    ),
                ),
                ("date", models.DateField(help_text="What date?", verbose_name="Date")),
                (
                    "camp",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        to="camps.Camp",
                        help_text="Which camp does this day belong to.",
                        verbose_name="Camp",
                    ),
                ),
            ],
            options={"verbose_name_plural": "Days", "verbose_name": "Day"},
        ),
        migrations.CreateModel(
            name="Expense",
            fields=[
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        serialize=False,
                        editable=False,
                        primary_key=True,
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        max_length=255,
                        help_text="What this expense covers.",
                        verbose_name="Description",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        max_digits=7,
                        help_text="The amount of the expense.",
                        verbose_name="Amount",
                        decimal_places=2,
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        max_length=3,
                        choices=[
                            ("btc", "BTC"),
                            ("dkk", "DKK"),
                            ("eur", "EUR"),
                            ("sek", "SEK"),
                        ],
                        help_text="What currency the amount is in.",
                        verbose_name="Currency",
                    ),
                ),
                (
                    "camp",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        to="camps.Camp",
                        help_text="The camp to which this expense relates to.",
                        verbose_name="Camp",
                    ),
                ),
                (
                    "covered_by",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                        blank=True,
                        help_text="Which user, if any, covered this expense.",
                        verbose_name="Covered by",
                        null=True,
                    ),
                ),
            ],
            options={"verbose_name_plural": "Expenses", "verbose_name": "Expense"},
        ),
        migrations.CreateModel(
            name="Signup",
            fields=[
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        serialize=False,
                        editable=False,
                        primary_key=True,
                    ),
                ),
                (
                    "cost",
                    models.DecimalField(
                        default=1500.0,
                        decimal_places=2,
                        help_text="What the user should/is willing to pay for this signup.",
                        verbose_name="Cost",
                        max_digits=7,
                    ),
                ),
                (
                    "paid",
                    models.BooleanField(
                        help_text="Whether the user has paid.",
                        verbose_name="Paid?",
                        default=False,
                    ),
                ),
                (
                    "camp",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        to="camps.Camp",
                        help_text="The camp that has been signed up for.",
                        verbose_name="Camp",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                        help_text="The user that has signed up.",
                        verbose_name="User",
                    ),
                ),
            ],
            options={"verbose_name_plural": "Signups", "verbose_name": "Signup"},
        ),
    ]
