from django.db import models
from django.utils.text import slugify

from utils.models import CampRelatedModel


class Team(CampRelatedModel):

    class Meta:
        ordering = ['name']
        unique_together = ('slug', 'camp')

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    camp = models.ForeignKey('camps.Camp')
    description = models.TextField()
    members = models.ManyToManyField('auth.User', through='teams.TeamMember')
    sub_team_of = models.ForeignKey('self', null=True, blank=True, related_name="sub_teams")

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

class TeamMember(models.Model):
    user = models.ForeignKey('auth.User')
    team = models.ForeignKey('teams.Team')
    responsible = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({})'.format(self.user, self.team)
