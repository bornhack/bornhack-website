from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from teams.models import Team
from utils.models import CreatedUpdatedModel


class Type(ExportModelOperationsMixin("type"), CreatedUpdatedModel):
    """The events.Type model contains different types of system events which can happen.
    New event types should be added in data migrations.
    The following types are currently used in the codebase:
    - ticket_created: Whenever a new ShopTicket is created
    - public_credit_name_changed: Whenever a user changes public_credit_name in the profile
    """

    name = models.TextField(unique=True, help_text="The type of event")

    irc_notification = models.BooleanField(
        default=False,
        help_text="Check to send IRC notifications for this type of event.",
    )

    email_notification = models.BooleanField(
        default=False,
        help_text="Check to send email notifications for this type of event.",
    )

    def __str__(self):
        return self.name

    @property
    def teams(self):
        """This property returns a queryset with all the teams that should receive this type of events"""
        team_ids = Routing.objects.filter(eventtype=self).values_list("team", flat=True)
        return Team.objects.filter(pk__in=team_ids)


class Routing(ExportModelOperationsMixin("routing"), CreatedUpdatedModel):
    """The events.Routing model contains routings for system events.
    Add a new entry to route events of a certain type to a team.
    Several teams can receive the same type of event.
    """

    eventtype = models.ForeignKey(
        "events.Type",
        related_name="eventroutes",
        on_delete=models.PROTECT,
        help_text="The type of event to route",
    )

    team = models.ForeignKey(
        "teams.Team",
        related_name="eventroutes",
        on_delete=models.PROTECT,
        help_text="The team which should receive events of this type.",
    )

    def __str__(self):
        return f"{self.eventtype} -> {self.team}"
