"""All models for teams application."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models
from django.urls import reverse_lazy
from django_prometheus.models import ExportModelOperationsMixin

from camps.models import Permission as CampPermission
from utils.models import CampRelatedModel
from utils.models import CreatedUpdatedModel
from utils.models import UUIDModel
from utils.slugs import unique_slugify

from .exceptions import IrcChannelInUseError
from .exceptions import ReservedIrcNameError

if TYPE_CHECKING:
    from typing import ClassVar

    from django.db.models import QuerySet

    from camps.models import Camp

logger = logging.getLogger(f"bornhack.{__name__}")


TEAM_GUIDE_TEMPLATE = """
## Preparations

...

## Camp setup

...

## During camp

...

## Takedown

...

## Notes for next year

 1. Remember to take notes
 1. ...
"""


class Team(ExportModelOperationsMixin("team"), CampRelatedModel):
    """Model for team."""
    camp = models.ForeignKey(
        "camps.Camp",
        related_name="teams",
        on_delete=models.PROTECT,
    )

    name = models.CharField(max_length=255, help_text="The team name")

    lead_group = models.OneToOneField(
        Group,
        blank=True,
        on_delete=models.PROTECT,
        related_name="team_lead",
        help_text="The django group carrying the team lead permissions for this team.",
    )

    member_group = models.OneToOneField(
        Group,
        blank=True,
        on_delete=models.CASCADE,
        related_name="team_member",
        help_text="The django group carrying the team permissions for this team.",
    )

    mapper_group = models.OneToOneField(
        Group,
        blank=True,
        on_delete=models.PROTECT,
        related_name="team_mapper",
        help_text="The django group carrying the team mapper permissions for this team.",
    )

    facilitator_group = models.OneToOneField(
        Group,
        blank=True,
        on_delete=models.PROTECT,
        related_name="team_facilitator",
        help_text="The django group carrying the team facilitator permissions for this team.",
    )

    infopager_group = models.OneToOneField(
        Group,
        blank=True,
        on_delete=models.PROTECT,
        related_name="team_infopager",
        help_text="The django group carrying the team infopager permissions for this team.",
    )

    pos_group = models.OneToOneField(
        Group,
        blank=True,
        on_delete=models.PROTECT,
        related_name="team_pos",
        help_text="The django group carrying the team pos permissions for this team.",
    )

    tasker_group = models.OneToOneField(
        Group,
        blank=True,
        on_delete=models.PROTECT,
        related_name="team_tasker",
        help_text="The django group carrying the team tasker permissions for this team.",
    )

    slug = models.SlugField(
        max_length=255,
        blank=True,
        help_text="Url slug for this team. Leave blank to generate based on team name",
    )

    shortslug = models.SlugField(
        help_text="Abbreviated version of the slug. Used in places like IRC channel names where space is limited",
    )

    description = models.TextField()

    needs_members = models.BooleanField(
        default=True,
        help_text="Check to indicate that this team needs more members",
    )

    members = models.ManyToManyField(
        "auth.User",
        related_name="teams",
        through="teams.TeamMember",
    )

    # mailing list related fields
    mailing_list = models.EmailField(blank=True)

    mailing_list_archive_public = models.BooleanField(
        default=False,
        help_text="Check if the mailing list archive is public",
    )

    mailing_list_nonmember_posts = models.BooleanField(
        default=False,
        help_text="Check if the mailinglist allows non-list-members to post",
    )

    # IRC related fields
    public_irc_channel_name = models.CharField(
        blank=True,
        null=True,
        unique=True,
        max_length=50,
        help_text="The public IRC channel for this team. Will be shown on the team page so people know "
        "how to reach the team. Leave empty if the team has no public IRC channel.",
    )
    public_irc_channel_bot = models.BooleanField(
        default=False,
        help_text="Check to make the bot join the teams public IRC channel. "
        "Leave unchecked to disable the IRC bot for this channel.",
    )
    public_irc_channel_managed = models.BooleanField(
        default=False,
        help_text="Check to make the bot manage the teams public IRC channel by registering it with NickServ "
        "and setting +Oo for all teammembers.",
    )
    public_irc_channel_fix_needed = models.BooleanField(
        default=False,
        help_text="Used to indicate to the IRC bot that this teams public IRC channel is in need of a "
        "permissions and ACL fix.",
    )

    private_irc_channel_name = models.CharField(
        blank=True,
        null=True,
        unique=True,
        max_length=50,
        help_text="The private IRC channel for this team. Will be shown to team members on the team page. "
        "Leave empty if the team has no private IRC channel.",
    )
    private_irc_channel_bot = models.BooleanField(
        default=False,
        help_text="Check to make the bot join the teams private IRC channel. "
        "Leave unchecked to disable the IRC bot for this channel.",
    )
    private_irc_channel_managed = models.BooleanField(
        default=False,
        help_text="Check to make the bot manage the private IRC channel by registering it with NickServ, "
        "setting +I and maintaining the ACL.",
    )
    private_irc_channel_fix_needed = models.BooleanField(
        default=False,
        help_text="Used to indicate to the IRC bot that this teams private IRC channel is in need of a "
        "permissions and ACL fix.",
    )

    # Signal
    public_signal_channel_link = models.URLField(null=True, blank=True, default="")
    private_signal_channel_link = models.URLField(null=True, blank=True, default="")

    shifts_enabled = models.BooleanField(
        default=False,
        help_text="Does this team have shifts? This enables defining shifts for this team.",
    )

    class Meta:
        """Meta."""
        ordering: ClassVar[list[str]] = ["name"]
        unique_together = (("name", "camp"), ("slug", "camp"))

    guide = models.TextField(
        blank=True,
        help_text="HowTo guide for this year (and next year)",
        verbose_name="team guide (Markdown)",
        default=TEAM_GUIDE_TEMPLATE,
    )

    def __str__(self) -> str:
        """Method to return a str of the model."""
        return f"{self.name} ({self.camp})"

    def get_absolute_url(self) -> str:
        """Method to return the absolute URL."""
        return reverse_lazy(
            "teams:general",
            kwargs={"camp_slug": self.camp.slug, "team_slug": self.slug},
        )

    def save(self, **kwargs) -> None:
        """Method for generating slugs and add groups if needed."""
        # generate slug if needed
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(camp=self.camp).values_list(
                    "slug",
                    flat=True,
                ),
            )

        # set shortslug if needed
        if not self.shortslug:
            self.shortslug = self.slug

        # generate permission groups for this team if needed
        for perm in settings.BORNHACK_TEAM_PERMISSIONS.keys():
            fk = f"{perm}_group"
            if not hasattr(self, fk):
                group, created = Group.objects.get_or_create(name=f"{self.camp.slug}-{self.slug}-team-{perm}")
                if created:
                    logger.info(f"Created group {group} for team {self}")
                setattr(self, fk, group)
        super().save(**kwargs)

    def clean(self) -> None:
        """Method for cleaning data."""
        # make sure the public irc channel name is prefixed with a # if it is set
        if self.public_irc_channel_name and self.public_irc_channel_name[0] != "#":
            self.public_irc_channel_name = f"#{self.public_irc_channel_name}"

        # make sure the private irc channel name is prefixed with a # if it is set
        if self.private_irc_channel_name and self.private_irc_channel_name[0] != "#":
            self.private_irc_channel_name = f"#{self.private_irc_channel_name}"

        # make sure the channel names are not reserved
        if self.public_irc_channel_name in (settings.IRCBOT_PUBLIC_CHANNEL, settings.IRCBOT_VOLUNTEER_CHANNEL):
            raise ReservedIrcNameError
        if self.private_irc_channel_name in (settings.IRCBOT_PUBLIC_CHANNEL, settings.IRCBOT_VOLUNTEER_CHANNEL):
            raise ReservedIrcNameError

        # make sure public_irc_channel_name is not in use as public or private irc channel for another team,
        # case insensitive
        if self.public_irc_channel_name and (
            Team.objects.filter(
                private_irc_channel_name__iexact=self.public_irc_channel_name,
            )
            .exclude(pk=self.pk)
            .exists()
            or Team.objects.filter(
                public_irc_channel_name__iexact=self.public_irc_channel_name,
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise IrcChannelInUseError

        # make sure private_irc_channel_name is not in use as public or private irc channel for another team,
        # case insensitive
        if self.private_irc_channel_name and (
            Team.objects.filter(
                private_irc_channel_name__iexact=self.private_irc_channel_name,
            )
            .exclude(pk=self.pk)
            .exists()
            or Team.objects.filter(
                public_irc_channel_name__iexact=self.private_irc_channel_name,
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise IrcChannelInUseError

    @property
    def memberships(self) -> QuerySet:
        """Returns all TeamMember objects for this team.

        Use self.members.all() to get User objects for all members,
        or use self.memberships.all() to get TeamMember objects for all members.
        """
        return TeamMember.objects.filter(team=self)

    @property
    def approved_members(self) -> QuerySet:
        """Returns only approved members (returns User objects, not TeamMember objects)."""
        return self.members.filter(teammember__approved=True)

    @property
    def unapproved_members(self) -> QuerySet:
        """Returns only unapproved members (returns User objects, not TeamMember objects)."""
        return self.members.filter(teammember__approved=False)

    @property
    def leads(self) -> QuerySet:
        """Return only approved team leads.

        Used to handle permissions for team leads.
        """
        return self.members.filter(
            teammember__approved=True,
            teammember__lead=True,
        )

    @property
    def regular_members(self) -> QuerySet:
        """Return only approved and not lead members with an approved public_credit_name.

        Used on the people pages.
        """
        return self.members.filter(
            teammember__approved=True,
            teammember__lead=False,
        )

    @property
    def unnamed_members(self) -> QuerySet:
        """Returns only approved and not team lead members, without an approved public_credit_name."""
        return self.members.filter(
            teammember__approved=True,
            teammember__lead=False,
            profile__public_credit_name_approved=False,
        )

    @property
    def member_permission_set(self) -> str:
        """Method for returning the team member permission set."""
        return f"camps.{self.slug}_team_member"

    @property
    def mapper_permission_set(self) -> str:
        """Method for returning the mapper permission set."""
        return f"camps.{self.slug}_team_mapper"

    @property
    def facilitator_permission_set(self) -> str:
        """Method for returning the facilitator permission set."""
        return f"camps.{self.slug}_team_facilitator"

    @property
    def lead_permission_set(self) -> str:
        """Method for returning the team lead permission set."""
        return f"camps.{self.slug}_team_lead"

    @property
    def pos_permission_set(self) -> str:
        """Method for returning the pos permission set."""
        return f"camps.{self.slug}_team_pos"

    @property
    def infopager_permission_set(self) -> str:
        """Method for returning the infopager permission set."""
        return f"camps.{self.slug}_team_infopager"

    @property
    def tasker_permission_set(self) -> str:
        """Method for returning the tasker permission set."""
        return f"camps.{self.slug}_team_tasker"


class TeamMember(ExportModelOperationsMixin("team_member"), CampRelatedModel):
    """Model for team member."""
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        help_text="The User object this team membership relates to",
    )

    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        help_text="The Team this membership relates to",
    )

    approved = models.BooleanField(
        default=False,
        help_text="True if this membership is approved. False if not.",
    )

    lead = models.BooleanField(
        default=False,
        help_text="True if this teammember is responsible for this Team. False if not.",
    )

    irc_acl_fix_needed = models.BooleanField(
        default=False,
        help_text="Maintained by the IRC bot, manual editing should not be needed. "
        "Will be set to true when a teammember sets or changes NickServ username, "
        "and back to false after the ACL has been fixed by the bot.",
    )

    class Meta:
        """Meta."""
        ordering: ClassVar[list[str]] = ["-lead", "-approved"]

    def __str__(self) -> str:
        """Method for returning str of model."""
        return "{} is {} {} member of team {}".format(
            self.user,
            "" if self.approved else "an unapproved",
            "" if not self.lead else "a lead",
            self.team,
        )

    @property
    def camp(self) -> Camp:
        """All CampRelatedModels must have a camp FK or a camp property."""
        return self.team.camp

    camp_filter = "team__camp"

    def update_group_membership(self, deleted=False) -> None:
        """Ensure group membership for this team membership is correct.

        When approved=True and deleted=False this means making sure the user is in team.member_group and
        if the membership has lead=True then also team.lead_group

        When deleted=True or approved=False loop over all of settings.BORNHACK_TEAM_PERMISSIONS.keys()
        and make sure user is not in any of the groups.
        """
        if self.approved and not deleted:
            logger.debug(f"Making sure user {self.user} is a member of group {self.team.member_group}")
            self.team.member_group.user_set.add(self.user)
            if self.lead:
                logger.debug(f"Making sure user {self.user} is a member of group {self.team.lead_group}")
                self.team.lead_group.user_set.add(self.user)
            else:
                logger.debug(f"Making sure user {self.user} is not a member of group {self.team.lead_group}")
                self.team.lead_group.user_set.remove(self.user)
        else:
            # membership deleted, remove membership of all team groups
            for perm in settings.BORNHACK_TEAM_PERMISSIONS.keys():
                group = getattr(self.team, f"{perm}_group")
                logger.debug(f"Making sure user {self.user} is not a member of group {group}")
                group.user_set.remove(self.user)


class TeamTask(ExportModelOperationsMixin("team_task"), CampRelatedModel):
    """Model for team tasks."""
    team = models.ForeignKey(
        "teams.Team",
        related_name="tasks",
        on_delete=models.PROTECT,
        help_text="The team this task belongs to",
    )
    name = models.CharField(max_length=100, help_text="Short name of this task")
    slug = models.SlugField(
        max_length=255,
        blank=True,
        help_text="url slug, leave blank to autogenerate",
    )
    description = models.TextField(
        help_text="Description of the task. Markdown is supported.",
    )
    when = DateTimeRangeField(
        blank=True,
        null=True,
        help_text="When does this task need to be started and/or finished?",
    )
    completed = models.BooleanField(
        help_text="Check to mark this task as completed.",
        default=False,
    )

    class Meta:
        """Meta."""
        ordering: ClassVar[list[str]] = ["completed", "when", "name"]
        unique_together = (("name", "team"), ("slug", "team"))

    def get_absolute_url(self) -> str:
        """Get the absolute URL for this model."""
        return reverse_lazy(
            "teams:task_detail",
            kwargs={
                "camp_slug": self.team.camp.slug,
                "team_slug": self.team.slug,
                "slug": self.slug,
            },
        )

    @property
    def camp(self) -> Camp:
        """All CampRelatedModels must have a camp FK or a camp property."""
        return self.team.camp

    camp_filter = "team__camp"

    def save(self, **kwargs) -> None:
        """Method for generating the slug if needed."""
        # generate slug if needed
        if not self.slug:
            self.slug = unique_slugify(
                self.name,
                slugs_in_use=self.__class__.objects.filter(team=self.team).values_list(
                    "slug",
                    flat=True,
                ),
            )
        super().save(**kwargs)


class TaskComment(
    ExportModelOperationsMixin("task_comment"),
    UUIDModel,
    CreatedUpdatedModel,
):
    """Model for task comments."""
    task = models.ForeignKey(
        "teams.TeamTask",
        on_delete=models.PROTECT,
        related_name="comments",
    )
    author = models.ForeignKey("teams.TeamMember", on_delete=models.PROTECT)
    comment = models.TextField()


class TeamShift(ExportModelOperationsMixin("team_shift"), CampRelatedModel):
    """Model for team shifts."""
    class Meta:
        """Meta."""
        ordering = ("shift_range",)

    team = models.ForeignKey(
        "teams.Team",
        related_name="shifts",
        on_delete=models.PROTECT,
        help_text="The team this shift belongs to",
    )

    shift_range = DateTimeRangeField()

    team_members = models.ManyToManyField(TeamMember, blank=True)

    people_required = models.IntegerField(default=1)

    @property
    def camp(self) -> Camp:
        """All CampRelatedModels must have a camp FK or a camp property."""
        return self.team.camp

    camp_filter = "team__camp"

    def __str__(self) -> str:
        """Method for returning a string of this model."""
        return f"{self.team.name} team shift from {self.shift_range.lower} to {self.shift_range.upper}"

    @property
    def users(self) -> list[TeamMember]:
        """Returns a list of team members on this shift."""
        return [member.user for member in self.team_members.all()]
