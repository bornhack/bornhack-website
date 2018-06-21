from django.db import models
from utils.models import UUIDModel, CreatedUpdatedModel
from program.models import EventType, EventLocation
from django.contrib.postgres.fields import DateTimeRangeField
from psycopg2.extras import DateTimeTZRange
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


class Camp(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = 'Camp'
        verbose_name_plural = 'Camps'
        ordering = ['-title']

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

    shortslug = models.SlugField(
        verbose_name='Short Slug',
        help_text='Abbreviated version of the slug. Used in IRC channel names and other places with restricted name length.',
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

    read_only = models.BooleanField(
        help_text='Whether the camp is read only (i.e. in the past)',
        default=False
    )

    colour = models.CharField(
        verbose_name='Colour',
        help_text='The primary colour for the camp in hex',
        max_length=7
    )

    call_for_participation_open = models.BooleanField(
        help_text='Check if the Call for Participation is open for this camp',
        default=False,
    )

    call_for_participation = models.TextField(
        blank=True,
        help_text='The CFP markdown for this Camp',
        default='The Call For Participation for this Camp has not been written yet',
    )

    call_for_sponsors_open = models.BooleanField(
        help_text='Check if the Call for Sponsors is open for this camp',
        default=False,
    )

    call_for_sponsors = models.TextField(
        blank=True,
        help_text='The CFS markdown for this Camp',
        default='The Call For Sponsors for this Camp has not been written yet',
    )

    def get_absolute_url(self):
        return reverse('camp_detail', kwargs={'camp_slug': self.slug})

    def clean(self):
        ''' Make sure the dates make sense - meaning no overlaps and buildup before camp before teardown '''
        errors = []
        # check for overlaps buildup vs. camp
        if self.buildup.upper > self.camp.lower:
            msg = "End of buildup must not be after camp start"
            errors.append(ValidationError({'buildup', msg}))
            errors.append(ValidationError({'camp', msg}))

        # check for overlaps camp vs. teardown
        if self.camp.upper > self.teardown.lower:
            msg = "End of camp must not be after teardown start"
            errors.append(ValidationError({'camp', msg}))
            errors.append(ValidationError({'teardown', msg}))

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return "%s - %s" % (self.title, self.tagline)

    @property
    def event_types(self):
        """ Return all event types with at least one event in this camp """
        return EventType.objects.filter(event__instances__isnull=False, event__camp=self).distinct()

    @property
    def event_locations(self):
        ''' Return all event locations with at least one event in this camp'''
        return EventLocation.objects.filter(eventinstances__isnull=False, camp=self).distinct()

    @property
    def logo_small(self):
        return 'img/%(slug)s/logo/%(slug)s-logo-s.png' % {'slug': self.slug}

    @property
    def logo_small_svg(self):
        return 'img/%(slug)s/logo/%(slug)s-logo-small.svg' % {'slug': self.slug}

    @property
    def logo_large(self):
        return 'img/%(slug)s/logo/%(slug)s-logo-l.png' % {'slug': self.slug}

    @property
    def logo_large_svg(self):
        return 'img/%(slug)s/logo/%(slug)s-logo-large.svg' % {'slug': self.slug}

    def get_days(self, camppart):
        '''
        Returns a list of DateTimeTZRanges representing the days during the specified part of the camp.
        '''
        if not hasattr(self, camppart):
            logger.error("nonexistant field/attribute")
            return False

        field = getattr(self, camppart)

        if not hasattr(field, '__class__') or not hasattr(field.__class__, '__name__') or not field.__class__.__name__ == 'DateTimeTZRange':
            logger.error("this attribute is not a datetimetzrange field: %s" % field)
            return False

        daycount = (field.upper - field.lower).days
        days = []
        for i in range(0, daycount):
            if i == 0:
                # on the first day use actual start time instead of midnight
                days.append(
                    DateTimeTZRange(
                        field.lower,
                        (field.lower+timedelta(days=i+1)).replace(hour=0)
                    )
                )
            elif i == daycount-1:
                # on the last day use actual end time instead of midnight
                days.append(
                    DateTimeTZRange(
                        (field.lower+timedelta(days=i)).replace(hour=0),
                        field.lower+timedelta(days=i+1)
                    )
                )
            else:
                # neither first nor last day, goes from midnight to midnight
                days.append(
                    DateTimeTZRange(
                        (field.lower+timedelta(days=i)).replace(hour=0),
                        (field.lower+timedelta(days=i+1)).replace(hour=0)
                    )
                )
        return days

    @property
    def buildup_days(self):
        '''
        Returns a list of DateTimeTZRanges representing the days during the buildup.
        '''
        return self.get_days('buildup')

    @property
    def camp_days(self):
        '''
        Returns a list of DateTimeTZRanges representing the days during the camp.
        '''
        return self.get_days('camp')

    @property
    def teardown_days(self):
        '''
        Returns a list of DateTimeTZRanges representing the days during the buildup.
        '''
        return self.get_days('teardown')

