# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "uuid",
                    models.UUIDField(
                        serialize=False,
                        editable=False,
                        primary_key=True,
                        default=uuid.uuid4,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=models.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                        help_text="The django user this profile belongs to.",
                        verbose_name="User",
                    ),
                ),
            ],
            options={"verbose_name_plural": "Profiles", "verbose_name": "Profile"},
        )
    ]
