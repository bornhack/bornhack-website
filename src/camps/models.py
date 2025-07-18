from __future__ import annotations

import logging
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import DateTimeRangeField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin
from psycopg2.extras import DateTimeTZRange

from tickets.models import PrizeTicket
from tickets.models import ShopTicket
from tickets.models import SponsorTicket
from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel

logger = logging.getLogger(f"bornhack.{__name__}")


class Permission(ExportModelOperationsMixin("permission"), models.Model):
    """An unmanaged field-less model which holds our non-model permissions (such as team permission sets)."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            # economy
            ("expense_create_permission", "Expense Create permission"),
            ("revenue_create_permission", "Revenue Create permission"),
        )


class Camp(ExportModelOperationsMixin("camp"), CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = "Camp"
        verbose_name_plural = "Camps"
        ordering = ["-title"]

    title = models.CharField(
        verbose_name="Title",
        help_text="Title of the camp, ie. Bornhack 2016.",
        max_length=255,
    )

    tagline = models.CharField(
        verbose_name="Tagline",
        help_text='Tagline of the camp, ie. "Initial Commit"',
        max_length=255,
    )

    slug = models.SlugField(
        verbose_name="Url Slug",
        help_text="The url slug to use for this camp",
    )

    shortslug = models.SlugField(
        verbose_name="Short Slug",
        help_text="Abbreviated version of the slug. Used in IRC channel names and other places with restricted name length.",
    )

    kickoff = DateTimeRangeField(
        null=True,
        blank=True,
        verbose_name="Camp Kickoff",
        help_text="The camp kickoff period.",
    )

    buildup = DateTimeRangeField(
        verbose_name="Buildup Period",
        help_text="The camp buildup period.",
    )

    camp = DateTimeRangeField(verbose_name="Camp Period", help_text="The camp period.")

    teardown = DateTimeRangeField(
        verbose_name="Teardown period",
        help_text="The camp teardown period.",
    )

    read_only = models.BooleanField(
        help_text="Whether the camp is read only (i.e. in the past)",
        default=False,
    )

    colour = models.CharField(
        verbose_name="Colour",
        help_text="The primary colour for the camp in hex",
        max_length=7,
    )

    light_text = models.BooleanField(
        default=True,
        help_text="Check if this camps colour requires white text, uncheck if black text is better",
    )

    call_for_participation_open = models.BooleanField(
        help_text="Check if the Call for Participation is open for this camp",
        default=False,
    )

    call_for_participation = models.TextField(
        blank=True,
        help_text="The CFP markdown for this Camp",
        default="The Call For Participation for this Camp has not been written yet",
    )

    call_for_sponsors_open = models.BooleanField(
        help_text="Check if the Call for Sponsors is open for this camp",
        default=False,
    )

    call_for_sponsors = models.TextField(
        blank=True,
        help_text="The CFS markdown for this Camp",
        default="The Call For Sponsors for this Camp has not been written yet",
    )

    show_schedule = models.BooleanField(
        help_text="Check if the schedule should be shown.",
        default=True,
    )

    economy_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        help_text="The economy team for this camp.",
        null=True,
        blank=True,
        related_name="+",
    )

    ticket_type_full_week_adult = models.ForeignKey(
        "tickets.TicketType",
        on_delete=models.SET_NULL,
        help_text="The ticket type for 'Adult Full Week' for this camp",
        null=True,
        blank=True,
        related_name="full_week_adult_camps",
    )

    ticket_type_one_day_adult = models.ForeignKey(
        "tickets.TicketType",
        on_delete=models.SET_NULL,
        help_text="The ticket type for 'Adult One Day' for this camp",
        null=True,
        blank=True,
        related_name="one_day_adult_camps",
    )

    ticket_type_full_week_child = models.ForeignKey(
        "tickets.TicketType",
        on_delete=models.SET_NULL,
        help_text="The ticket type for 'Child Full Week' for this camp",
        null=True,
        blank=True,
        related_name="full_week_child_camps",
    )

    ticket_type_one_day_child = models.ForeignKey(
        "tickets.TicketType",
        on_delete=models.SET_NULL,
        help_text="The ticket type for 'Child One Day' for this camp",
        null=True,
        blank=True,
        related_name="one_day_child_camps",
    )

    def get_absolute_url(self):
        return reverse("camp_detail", kwargs={"camp_slug": self.slug})

    def clean(self) -> None:
        """Make sure the dates make sense - meaning no overlaps and buildup before camp before teardown."""
        errors = []
        # check for overlaps buildup vs. camp
        if self.buildup.upper > self.camp.lower:
            msg = "End of buildup must not be after camp start"
            errors.append(ValidationError({"buildup", msg}))
            errors.append(ValidationError({"camp", msg}))

        # check for overlaps camp vs. teardown
        if self.camp.upper > self.teardown.lower:
            msg = "End of camp must not be after teardown start"
            errors.append(ValidationError({"camp", msg}))
            errors.append(ValidationError({"teardown", msg}))

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"{self.title} - {self.tagline}"

    def activate_team_permissions(self) -> None:
        """Add permissions to this camps teams."""
        permission_content_type = ContentType.objects.get_for_model(Permission)
        for team in self.teams.all():
            for perm in settings.BORNHACK_TEAM_PERMISSIONS.keys():
                fk = f"{perm}_group"
                permission = DjangoPermission.objects.get(
                    content_type=permission_content_type,
                    codename=f"{team.slug}_team_{perm}",
                )
                group = getattr(team, fk)
                group.permissions.add(permission)
                logger.debug(f"Added permission {permission} to group {group}")

    def deactivate_team_permissions(self) -> None:
        """Add permissions to this camps teams."""
        permission_content_type = ContentType.objects.get_for_model(Permission)
        for team in self.teams.all():
            for perm in settings.BORNHACK_TEAM_PERMISSIONS.keys():
                fk = f"{perm}_group"
                permission = DjangoPermission.objects.get(
                    content_type=permission_content_type,
                    codename=f"{team.slug}_team_{perm}",
                )
                group = getattr(team, fk)
                group.permissions.remove(permission)
                logger.debug(f"Removed permission {permission} from group {group}")

    @property
    def logo_small(self) -> str:
        return f"img/{self.slug}/logo/{self.slug}-logo-s.png"

    @property
    def logo_small_svg(self) -> str:
        return f"img/{self.slug}/logo/{self.slug}-logo-small.svg"

    @property
    def logo_large(self) -> str:
        return f"img/{self.slug}/logo/{self.slug}-logo-l.png"

    @property
    def logo_large_svg(self) -> str:
        return f"img/{self.slug}/logo/{self.slug}-logo-large.svg"

    def get_days(self, camppart):
        """Returns a list of DateTimeTZRanges representing the days during the specified part of the camp."""
        if not hasattr(self, camppart):
            logger.error("nonexistant field/attribute")
            return False

        field = getattr(self, camppart)

        if (
            not hasattr(field, "__class__")
            or not hasattr(field.__class__, "__name__")
            or field.__class__.__name__ != "DateTimeTZRange"
        ):
            logger.error(f"this attribute is not a datetimetzrange field: {field}")
            return False

        # count how many unique dates we have in this range
        daycount = 1
        while True:
            if field.lower.date() + timedelta(days=daycount) > field.upper.date():
                break
            daycount += 1

        # loop through the required number of days, append to list as we go
        days = []
        for i in range(daycount):
            if i == 0:
                # on the first day use actual start time instead of midnight (local time)
                days.append(
                    DateTimeTZRange(
                        timezone.localtime(field.lower),
                        timezone.localtime(
                            field.lower + timedelta(days=i + 1),
                        ).replace(hour=0),
                    ),
                )
            elif i == daycount - 1:
                # on the last day use actual end time instead of midnight (local time)
                days.append(
                    DateTimeTZRange(
                        timezone.localtime(field.lower + timedelta(days=i)).replace(
                            hour=0,
                        ),
                        timezone.localtime(field.lower + timedelta(days=i)),
                    ),
                )
            else:
                # neither first nor last day, goes from midnight to midnight (local time)
                days.append(
                    DateTimeTZRange(
                        timezone.localtime(field.lower + timedelta(days=i)).replace(
                            hour=0,
                        ),
                        timezone.localtime(
                            field.lower + timedelta(days=i + 1),
                        ).replace(hour=0),
                    ),
                )
        return days

    @property
    def buildup_days(self):
        """Returns a list of DateTimeTZRanges representing the days during the buildup."""
        return self.get_days("buildup")

    @property
    def camp_days(self):
        """Returns a list of DateTimeTZRanges representing the days during the camp."""
        return self.get_days("camp")

    @property
    def teardown_days(self):
        """Returns a list of DateTimeTZRanges representing the days during the buildup."""
        return self.get_days("teardown")

    # convenience properties to access Camp-related stuff easily from the Camp object

    @property
    def event_types(self):
        """Return all event types with at least one event in this camp."""
        EventType = apps.get_model("program", "EventType")
        return EventType.objects.filter(
            events__isnull=False,
            event__track__camp=self,
        ).distinct()

    @property
    def event_proposals(self):
        EventProposal = apps.get_model("program", "EventProposal")
        return EventProposal.objects.filter(track__camp=self)

    @property
    def events(self):
        Event = apps.get_model("program", "Event")
        return Event.objects.filter(track__camp=self)

    @property
    def event_sessions(self):
        EventSession = apps.get_model("program", "EventSession")
        return EventSession.objects.filter(camp=self)

    @property
    def event_slots(self):
        EventSlot = apps.get_model("program", "EventSlot")
        return EventSlot.objects.filter(event_session__in=self.event_sessions.all())

    @property
    def checked_in_full_week_adults(self) -> int:
        """Return the count of full week adult tickets checked in"""
        shop_tickets = (
            ShopTicket.objects.filter(
                ticket_type=self.ticket_type_full_week_adult,
            ).exclude(used_at=None)
        ).count()

        sponsor_tickets = (
            SponsorTicket.objects.filter(
                ticket_type=self.ticket_type_full_week_adult,
            ).exclude(used_at=None)
        ).count()

        prize_tickets = (
            PrizeTicket.objects.filter(
                ticket_type=self.ticket_type_full_week_adult,
            ).exclude(used_at=None)
        ).count()

        return shop_tickets + sponsor_tickets + prize_tickets

    @property
    def checked_in_full_week_children(self) -> int:
        """Return the count of full week children tickets checked in"""
        shop_tickets = (
            ShopTicket.objects.filter(
                ticket_type=self.ticket_type_full_week_child,
            ).exclude(used_at=None)
        ).count()

        sponsor_tickets = (
            SponsorTicket.objects.filter(
                ticket_type=self.ticket_type_full_week_child,
            ).exclude(used_at=None)
        ).count()

        prize_tickets = (
            PrizeTicket.objects.filter(
                ticket_type=self.ticket_type_full_week_child,
            ).exclude(used_at=None)
        ).count()

        return shop_tickets + sponsor_tickets + prize_tickets

    @property
    def checked_in_one_day_adults(self) -> int:
        """Return the count of todays one day adult tickets checked in.

        Count tickets with a checked in timestamp from 0600-0600 next day.
        Reason being early arriving participants might get checked in before 10.
        """
        now = timezone.localtime()
        today_06_hour = now.replace(hour=6, minute=0, second=0)
        if now < today_06_hour:
            start = today_06_hour - timezone.timedelta(days=1)
            end = today_06_hour
        else:
            start = today_06_hour
            end = today_06_hour + timezone.timedelta(days=1)

        shop_tickets = (
            ShopTicket.objects.filter(
                ticket_type=self.ticket_type_one_day_adult,
            ).filter(used_at__gte=start, used_at__lt=end)
        ).count()

        sponsor_tickets = (
            SponsorTicket.objects.filter(
                ticket_type=self.ticket_type_one_day_adult,
            ).filter(used_at__gte=start, used_at__lt=end)
        ).count()

        prize_tickets = (
            PrizeTicket.objects.filter(
                ticket_type=self.ticket_type_one_day_adult,
            ).filter(used_at__gte=start, used_at__lt=end)
        ).count()

        return shop_tickets + sponsor_tickets + prize_tickets

    @property
    def checked_in_one_day_children(self) -> int:
        """Return the count of todays one day children tickets checked in.

        Count tickets with a checked in timestamp from 0600-0600 next day.
        Reason being early arriving participants might get checked in before 10.
        """
        now = timezone.localtime()
        today_06_hour = now.replace(hour=6, minute=0, second=0)
        if now < today_06_hour:
            start = today_06_hour - timezone.timedelta(days=1)
            end = today_06_hour
        else:
            start = today_06_hour
            end = today_06_hour + timezone.timedelta(days=1)

        shop_tickets = (
            ShopTicket.objects.filter(
                ticket_type=self.ticket_type_one_day_child,
            ).filter(used_at__gte=start, used_at__lt=end)
        ).count()

        sponsor_tickets = (
            SponsorTicket.objects.filter(
                ticket_type=self.ticket_type_one_day_child,
            ).filter(used_at__gte=start, used_at__lt=end)
        ).count()

        prize_tickets = (
            PrizeTicket.objects.filter(
                ticket_type=self.ticket_type_one_day_child,
            ).filter(used_at__gte=start, used_at__lt=end)
        ).count()

        return shop_tickets + sponsor_tickets + prize_tickets

    @property
    def participant_count(self) -> int:
        """Retrieve the participant count for all used 'full week' tickets
        and todays used 'one day' tickets.
        """
        return (
            self.checked_in_full_week_adults
            + self.checked_in_full_week_children
            + self.checked_in_one_day_adults
            + self.checked_in_one_day_children
        )
