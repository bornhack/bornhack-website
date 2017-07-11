from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from utils.models import UUIDModel, CreatedUpdatedModel


class Profile(CreatedUpdatedModel, UUIDModel):
    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    user = models.OneToOneField(
        User,
        verbose_name=_('User'),
        help_text=_('The django user this profile belongs to.'),
    )

    name = models.CharField(
        max_length=200,
        default='',
        blank=True,
        help_text='Your name or handle'
    )

    description = models.TextField(
        default='',
        blank=True,
        help_text='Please include any info you think could be relevant, like drivers license, first aid certificates, crafts, skills and previous experience. Please also include availability if you are not there for the full week.',
    )

    public_credits = models.BooleanField(
        default=False,
        help_text='Check this box if you want your name to appear in the list of volunteers for this event. Please inform your team responsible what you would like to be credited as.'
    )

    public_credit_name = models.CharField(
        blank=True,
        max_length=100,
        help_text='The name used on the public list of volunteers for this event. Only used if public_credits is True. Not editable by users (to avoid getting junk on the website).'
    )

    @property
    def email(self):
        return self.user.email

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_profile(sender, created, instance, **kwargs):
    if created:
        Profile.objects.create(user=instance)

