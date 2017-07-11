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
        help_text='Your name or handle (only visible to team responsible and organisers)'
    )

    description = models.TextField(
        default='',
        blank=True,
        help_text='Please include any info you think could be relevant, like drivers license, first aid certificates, crafts, skills and previous experience. Please also include availability if you are not there for the full week.',
    )

    public_credit_name = models.CharField(
        blank=True,
        max_length=100,
        help_text='The name you want to appear on in the credits section of the public website (the People pages). Leave empty if you want no public credit.'
    )

    public_credit_name_approved = models.BooleanField(
        default=False,
        help_text='Check this box to approve this users public_credit_name. This will be unchecked automatically when the user edits public_credit_name'
    )

    @property
    def email(self):
        return self.user.email

    def __str__(self):
        return self.user.username

    def approve_public_credit_name(self):
        self.public_credit_name_approved = True
        self.save()

    @property
    def approved_public_credit_name(self):
        if self.public_credit_name_approved:
            return self.public_credit_name
        else:
            return False


@receiver(post_save, sender=User)
def create_profile(sender, created, instance, **kwargs):
    if created:
        Profile.objects.create(user=instance)

