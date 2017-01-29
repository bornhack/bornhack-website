import datetime
from django.db import models
from utils.models import UUIDModel, CreatedUpdatedModel
from program.models import EventType
from django.contrib.postgres.fields import DateTimeRangeField
from psycopg2.extras import DateTimeTZRange
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone


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

    def get_days(self, camppart):
        '''
        Returns a list of DateTimeTZRanges representing the days during the specified part of the camp.
        '''
        if not hasattr(self, camppart):
            print("nonexistant field/attribute")
            return False

        field = getattr(self, camppart)

        if not hasattr(field, '__class__') or not hasattr(field.__class__, '__name__') or not field.__class__.__name__ == 'DateTimeTZRange':
            print("this attribute is not a datetimetzrange field: %s" % field)
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

    @property
    def call_for_speakers_open(self):
        if self.camp.upper < timezone.now():
            return False
        else:
            return True

