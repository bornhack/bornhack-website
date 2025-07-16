from django.db import migrations, models
import django.db.models.deletion

def migrate_assignments(apps, schema_editor):
    TeamShift = apps.get_model("teams", "TeamShift")
    for teamshift in TeamShift.objects.all():
        members = teamshift.team_members.all()
        teamshift.team_members_new.set(members)
        teamshift.save()

class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0064_teamshiftassignment_teamshift_team_members_new'),
    ]

    operations = [
        migrations.RunPython(migrate_assignments),
    ]
