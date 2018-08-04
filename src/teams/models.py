from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from utils.models import CampRelatedModel
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.conf import settings
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class Team(CampRelatedModel):
    camp = models.ForeignKey(
        'camps.Camp',
        related_name="teams",
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        max_length=255,
        help_text='The team name',
    )

    slug = models.SlugField(
        max_length=255,
        blank=True,
        help_text='Url slug for this team. Leave blank to generate based on team name',
    )

    shortslug = models.SlugField(
        help_text='Abbreviated version of the slug. Used in places like IRC channel names where space is limited',
    )

    description = models.TextField()

    needs_members = models.BooleanField(
        default=True,
        help_text='Check to indicate that this team needs more members',
    )

    members = models.ManyToManyField(
        'auth.User',
        related_name='teams',
        through='teams.TeamMember'
    )

    # mailing list related fields
    mailing_list = models.EmailField(
        blank=True
    )

    mailing_list_archive_public = models.BooleanField(
        default=False,
        help_text='Check if the mailing list archive is public'
    )

    mailing_list_nonmember_posts = models.BooleanField(
        default=False,
        help_text='Check if the mailinglist allows non-list-members to post'
    )

    # IRC related fields
    public_irc_channel_name = models.CharField(
        blank=True,
        null=True,
        unique=True,
        max_length=50,
        help_text='The public IRC channel for this team. Will be shown on the team page so people know how to reach the team. Leave empty if the team has no public IRC channel.'
    )
    public_irc_channel_bot = models.BooleanField(
        default=False,
        help_text='Check to make the bot join the teams public IRC channel. Leave unchecked to disable the IRC bot for this channel.'
    )
    public_irc_channel_managed = models.BooleanField(
        default=False,
        help_text='Check to make the bot manage the teams public IRC channel by registering it with NickServ and setting +Oo for all teammembers.'
    )
    public_irc_channel_fix_needed = models.BooleanField(
        default=False,
        help_text='Used to indicate to the IRC bot that this teams public IRC channel is in need of a permissions and ACL fix.'
    )

    private_irc_channel_name = models.CharField(
        blank=True,
        null=True,
        unique=True,
        max_length=50,
        help_text='The private IRC channel for this team. Will be shown to team members on the team page. Leave empty if the team has no private IRC channel.'
    )
    private_irc_channel_bot = models.BooleanField(
        default=False,
        help_text='Check to make the bot join the teams private IRC channel. Leave unchecked to disable the IRC bot for this channel.'
    )
    private_irc_channel_managed = models.BooleanField(
        default=False,
        help_text='Check to make the bot manage the private IRC channel by registering it with NickServ, setting +I and maintaining the ACL.'
    )
    private_irc_channel_fix_needed = models.BooleanField(
        default=False,
        help_text='Used to indicate to the IRC bot that this teams private IRC channel is in need of a permissions and ACL fix.'
    )

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'camp'), ('slug', 'camp'))

    def __str__(self):
        return '{} ({})'.format(self.name, self.camp)

    def get_absolute_url(self):
        return reverse_lazy('teams:general', kwargs={'camp_slug': self.camp.slug, 'team_slug': self.slug})

    def save(self, **kwargs):
        # generate slug if needed
        if not self.pk or not self.slug:
            slug = slugify(self.name)
            self.slug = slug

        # set shortslug if needed
        if not self.shortslug:
            self.shortslug = self.slug

        super().save(**kwargs)

    def clean(self):
        # make sure the public irc channel name is prefixed with a # if it is set
        if self.public_irc_channel_name and self.public_irc_channel_name[0] != "#":
            self.public_irc_channel_name = "#%s" % self.public_irc_channel_name

        # make sure the private irc channel name is prefixed with a # if it is set
        if self.private_irc_channel_name and self.private_irc_channel_name[0] != "#":
            self.private_irc_channel_name = "#%s" % self.private_irc_channel_name

        # make sure the channel names are not reserved
        if self.public_irc_channel_name == settings.IRCBOT_PUBLIC_CHANNEL or self.public_irc_channel_name == settings.IRCBOT_VOLUNTEER_CHANNEL:
            raise ValidationError('The public IRC channel name is reserved')
        if self.private_irc_channel_name == settings.IRCBOT_PUBLIC_CHANNEL or self.private_irc_channel_name == settings.IRCBOT_VOLUNTEER_CHANNEL:
            raise ValidationError('The private IRC channel name is reserved')

        # make sure public_irc_channel_name is unique
        if self.public_irc_channel_name:
            if Team.objects.filter(private_irc_channel_name=self.public_irc_channel_name).exclude(pk=self.pk).exists():
                raise ValidationError('The public IRC channel name is already in use!')

        # make sure private_irc_channel_name is unique
        if self.private_irc_channel_name:
            if Team.objects.filter(public_irc_channel_name=self.private_irc_channel_name).exclude(pk=self.pk).exists():
                raise ValidationError('The private IRC channel name is already in use!')

    @property
    def memberships(self):
        """
        Returns all TeamMember objects for this team.
        Use self.members.all() to get User objects for all members,
        or use self.memberships.all() to get TeamMember objects for all members.
        """
        return TeamMember.objects.filter(
            team=self
        )

    @property
    def approved_members(self):
        """
        Returns only approved members (returns User objects, not TeamMember objects)
        """
        return self.members.filter(
            teammember__approved=True
        )

    @property
    def unapproved_members(self):
        """
        Returns only unapproved members (returns User objects, not TeamMember objects)
        """
        return self.members.filter(
            teammember__approved=False
        )

    @property
    def responsible_members(self):
        """
        Return only approved and responsible members
        Used to handle permissions for team management
        """
        return self.members.filter(
            teammember__approved=True,
            teammember__responsible=True
        )

    @property
    def regular_members(self):
        """
        Return only approved and not responsible members with
        an approved public_credit_name.
        Used on the people pages.
        """
        return self.members.filter(
            teammember__approved=True,
            teammember__responsible=False,
        )

    @property
    def unnamed_members(self):
        """
        Returns only approved and not responsible members,
        without an approved public_credit_name.
        """
        return self.members.filter(
            teammember__approved=True,
            teammember__responsible=False,
            profile__public_credit_name_approved=False
        )


class TeamMember(CampRelatedModel):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        help_text="The User object this team membership relates to",
    )

    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.PROTECT,
        help_text="The Team this membership relates to"
    )

    approved = models.BooleanField(
        default=False,
        help_text="True if this membership is approved. False if not."
    )

    responsible = models.BooleanField(
        default=False,
        help_text="True if this teammember is responsible for this Team. False if not."
    )

    irc_acl_fix_needed = models.BooleanField(
        default=False,
        help_text='Maintained by the IRC bot, manual editing should not be needed. Will be set to true when a teammember sets or changes NickServ username, and back to false after the ACL has been fixed by the bot.',
    )

    class Meta:
        ordering = ['-responsible', '-approved']

    def __str__(self):
        return '{} is {} {} member of team {}'.format(
            self.user,
            '' if self.approved else 'an unapproved',
            '' if not self.responsible else 'a responsible',
            self.team
        )

    @property
    def camp(self):
        """ All CampRelatedModels must have a camp FK or a camp property """
        return self.team.camp

    camp_filter = 'team__camp'


class TeamTask(CampRelatedModel):
    team = models.ForeignKey(
        'teams.Team',
        related_name='tasks',
        on_delete=models.PROTECT,
        help_text='The team this task belongs to',
    )
    name = models.CharField(
        max_length=100,
        help_text='Short name of this task',
    )
    slug = models.SlugField(
        max_length=255,
        blank=True,
        help_text='url slug, leave blank to autogenerate',
    )
    description = models.TextField(
        help_text='Description of the task. Markdown is supported.'
    )
    when = DateTimeRangeField(
        blank=True,
        null=True,
        help_text='When does this task need to be started and/or finished?'
    )
    completed = models.BooleanField(
        help_text='Check to mark this task as completed.',
        default=False
    )

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'team'), ('slug', 'team'))

    def get_absolute_url(self):
        return reverse_lazy('teams:task_detail', kwargs={'camp_slug': self.team.camp.slug, 'team_slug': self.team.slug, 'slug': self.slug})

    @property
    def camp(self):
        """ All CampRelatedModels must have a camp FK or a camp property """
        return self.team.camp

    camp_filter = 'team__camp'

    def save(self, **kwargs):
        # generate slug if needed
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(**kwargs)

