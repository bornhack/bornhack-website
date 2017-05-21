from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from utils.models import CampRelatedModel
from .email import add_new_membership_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class TeamArea(CampRelatedModel):
    class Meta:
        ordering = ['name']
        unique_together = ('name', 'camp')

    name = models.CharField(max_length=255)
    description = models.TextField(default='')
    camp = models.ForeignKey('camps.Camp')
    responsible = models.ManyToManyField(
        'auth.User',
        related_name='responsible_team_areas'
    )

    def __str__(self):
        return '{} ({})'.format(self.name, self.camp)


class Team(CampRelatedModel):
    class Meta:
        ordering = ['name']
        unique_together = (('name', 'camp'), ('slug', 'camp'))

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    camp = models.ForeignKey('camps.Camp')
    area = models.ForeignKey(
        'teams.TeamArea',
        related_name='teams',
        on_delete=models.PROTECT
    )
    description = models.TextField()
    needs_members = models.BooleanField(default=True)
    members = models.ManyToManyField(
        'auth.User',
        related_name='teams',
        through='teams.TeamMember'
    )

    def __str__(self):
        return '{} ({})'.format(self.name, self.camp)

    def save(self, **kwargs):
        if (
            not self.pk or
            not self.slug
        ):
            slug = slugify(self.name)
            self.slug = slug

        super().save(**kwargs)

    def clean(self):
        if self.camp != self.area.camp:
            raise ValidationError({'camp': 'camp is different from area.camp'})

    def memberstatus(self, member):
        if member not in self.members.all():
            return "Not member"
        else:
            if TeamMember.objects.get(team=self, user=member).approved:
                return "Member"
            else:
                return "Membership Pending"

    @property
    def responsible(self):
        if TeamMember.objects.filter(team=self, responsible=True).exists():
            return User.objects.filter(
                teammember__team=self,
                teammember__responsible=True
            )
        else:
            return self.area.responsible.all()


class TeamMember(models.Model):
    user = models.ForeignKey('auth.User')
    team = models.ForeignKey('teams.Team')
    approved = models.BooleanField(default=False)
    responsible = models.BooleanField(default=False)

    def __str__(self):
        return '{} is {} member of team {}'.format(
            self.user, '' if self.approved else 'an unapproved', self.team
        )


@receiver(post_save, sender=TeamMember)
def add_responsible_email(sender, instance, created, **kwargs):
    if created:
        if not add_new_membership_email(instance):
            logger.error('Error adding email to outgoing queue')
