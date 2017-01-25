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

    @property
    def email(self):
        return self.user.email

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_profile(sender, created, instance, **kwargs):
    if created:
        Profile.objects.create(user=instance)

