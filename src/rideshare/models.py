from django.db import models
from django.urls import reverse

from utils.models import UUIDModel, CampRelatedModel


class Ride(UUIDModel, CampRelatedModel):
    camp = models.ForeignKey('camps.Camp', on_delete=models.PROTECT)
    user = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    seats = models.PositiveIntegerField()
    location = models.CharField(max_length=100)
    when = models.DateTimeField()
    description = models.TextField()

    def get_absolute_url(self):
        return reverse(
            'rideshare:detail',
            kwargs={
                'pk': self.pk,
                'camp_slug': self.camp.slug
            }
        )
