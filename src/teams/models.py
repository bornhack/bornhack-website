from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from utils.models import CampRelatedModel
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.urls import reverse_lazy
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
    irc_channel = models.BooleanField(
        default=False,
        help_text='Check to make the IRC bot join the team IRC channel. Leave unchecked to disable IRC bot functionality for this team entirely.',
    )

    irc_channel_name = models.TextField(
        default='',
        blank=True,
        help_text='Team IRC channel. Leave blank to generate channel name automatically, based on camp shortslug and team shortslug.',
    )

    irc_channel_managed = models.BooleanField(
        default=True,
        help_text='Check to make the bot manage the team IRC channel. The bot will register the channel with ChanServ if possible, and manage ACLs as needed.',
    )

    irc_channel_private = models.BooleanField(
        default=True,
        help_text='Check to make the IRC channel secret and +i (private for team members only using an ACL). Leave unchecked to make the IRC channel public and open for everyone.'
    )

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'camp'), ('slug', 'camp'))

    def __str__(self):
        return '{} ({})'.format(self.name, self.camp)

    def save(self, **kwargs):
        # generate slug if needed
        if not self.pk or not self.slug:
            slug = slugify(self.name)
            self.slug = slug

        if not self.shortslug:
            self.shortslug = self.slug

        # generate IRC channel name if needed
        if self.irc_channel and not self.irc_channel_name:
            self.irc_channel_name = "#%s-%s" % (self.camp.shortslug, self.shortslug)

        super().save(**kwargs)

    def clean(self):
        # make sure the irc channel name is prefixed with a # if it is set
        if self.irc_channel_name and self.irc_channel_name[0] != "#":
            self.irc_channel_name = "#%s" % self.irc_channel_name

        if self.irc_channel_name:
            if Team.objects.filter(irc_channel_name=self.irc_channel_name).exclude(pk=self.pk).exists():
                raise ValidationError("This IRC channel name is already in use")

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

    irc_channel_acl_ok = models.BooleanField(
        default=False,
        help_text="Maintained by the IRC bot, do not edit manually. True if the teammembers NickServ username has been added to the Team IRC channels ACL.",
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

    class Meta:
        ordering = ['name']
        unique_together = (('name', 'team'), ('slug', 'team'))

    def get_absolute_url(self):
        return reverse_lazy('teams:task_detail', kwargs={'camp_slug': self.team.camp.slug, 'team_slug': self.team.slug, 'slug': self.slug})

    @property
    def camp(self):
        """ All CampRelatedModels must have a camp FK or a camp property """
        return self.team.camp

    def save(self, **kwargs):
        # generate slug if needed
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(**kwargs)

