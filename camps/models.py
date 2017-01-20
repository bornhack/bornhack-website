import datetime
from django.db import models
from utils.models import UUIDModel, CreatedUpdatedModel
from program.models import EventType
from django.contrib.postgres.fields import DateTimeRangeField


class Camp(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Camp'
        verbose_name_plural = 'Camps'

    title = models.CharField(
        verbose_name='Title',
        help_text='Title of the camp, ie. Bornhack 2016.',
        max_length=255,
    )

    tagline = models.CharField(
        verbose_name='Tagline',
        help_text='Tagline of the camp, ie. "Initial Commit"',
        max_length=255,
    )

    slug = models.SlugField(
        verbose_name='Url Slug',
        help_text='The url slug to use for this camp'
    )

    buildup = DateTimeRangeField(
        verbose_name='Buildup Period',
        help_text='The camp buildup period.',
    )

    camp = DateTimeRangeField(
        verbose_name='Camp Period',
        help_text='The camp period.',
    )

    teardown = DateTimeRangeField(
        verbose_name='Teardown period',
        help_text='The camp teardown period.',
    )

    def __unicode__(self):
        return "%s - %s" % (self.title, self.tagline)

    @property
    def event_types(self):
        # return all event types with at least one event in this camp
        return EventType.objects.filter(event__instances__isnull=False, event__camp=self).distinct()

    @property
    def logo_small(self):
        return 'img/%(slug)s/logo/%(slug)s-logo-small.png' % {'slug': self.slug}

    @property
    def logo_large(self):
        return 'img/%(slug)s/logo/%(slug)s-logo-large.png' % {'slug': self.slug}

