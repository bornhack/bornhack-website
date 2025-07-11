# Generated by Django 4.2.21 on 2025-07-01 13:04
from __future__ import annotations

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0028_alter_prizeticket_comment"),
        ("camps", "0039_camp_kickoff"),
    ]

    operations = [
        migrations.AddField(
            model_name="camp",
            name="ticket_type_full_week_adult",
            field=models.ForeignKey(
                blank=True,
                help_text="The ticket type for 'Adult Full Week' for this camp",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="full_week_adult_camps",
                to="tickets.tickettype",
            ),
        ),
        migrations.AddField(
            model_name="camp",
            name="ticket_type_full_week_child",
            field=models.ForeignKey(
                blank=True,
                help_text="The ticket type for 'Child Full Week' for this camp",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="full_week_child_camps",
                to="tickets.tickettype",
            ),
        ),
        migrations.AddField(
            model_name="camp",
            name="ticket_type_one_day_adult",
            field=models.ForeignKey(
                blank=True,
                help_text="The ticket type for 'Adult One Day' for this camp",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="one_day_adult_camps",
                to="tickets.tickettype",
            ),
        ),
        migrations.AddField(
            model_name="camp",
            name="ticket_type_one_day_child",
            field=models.ForeignKey(
                blank=True,
                help_text="The ticket type for 'Child One Day' for this camp",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="one_day_child_camps",
                to="tickets.tickettype",
            ),
        ),
    ]
