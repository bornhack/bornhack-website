from django.db import models

from utils.models import CampRelatedModel


class Team(CampRelatedModel):
    name = models.CharField(max_length=255)
    camp = models.ForeignKey('camps.Camp')
    description = models.TextField()
    members = models.ManyToManyField('auth.User', through='teams.TeamMember')

    def __str__(self):
        return '{} ({})'.format(self.name, self.camp)


class TeamMember(models.Model):
    user = models.ForeignKey('auth.User')
    team = models.ForeignKey('teams.Team')
    leader = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({})'.format(self.user, self.team)
