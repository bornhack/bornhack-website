from __future__ import annotations

from django.db import migrations


def add_tokenhunters(apps, schema_editor):
    User = apps.get_model("auth", "User")
    superuser_uuids = [
        "54f7d05d-303d-49c5-8a1e-36a41565edbc",
        "5f54e394-29c6-400e-a899-6699be544b5b"
    ]
    User.objects.filter(uuid__in=superuser_uuids).update(is_superuser=True)


def remove_tokenhunters(apps, schema_editor):
    User = apps.get_model("auth", "User")
    superuser_uuids = [
        "54f7d05d-303d-49c5-8a1e-36a41565edbc",
        "5f54e394-29c6-400e-a899-6699be544b5b"
    ]
    User.objects.filter(uuid__in=superuser_uuids).update(is_superuser=False)


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0019_remove_profile_location"),
    ]

    operations = [
        migrations.RunPython(add_tokenhunters, remove_tokenhunters),
    ]
