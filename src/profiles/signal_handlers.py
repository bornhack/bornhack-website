from django.db.models.signals import (
    post_save,
    pre_save
)
from events.handler import handle_team_event

def create_profile(sender, created, instance, **kwargs):
    """
    Signal handler called after a User object is saved.
    Creates a Profile object when the User object was just created.
    """
    from .models import Profile
    if created:
        Profile.objects.create(user=instance)


def changed_public_credit_name(sender, instance, **kwargs):
    """
    Signal handler called before a Profile object is saved.
    Checks if a users public_credit_name has been changed, and triggers a public_credit_name_changed event if so
    """
    try:
        original = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        # newly created object, do nothing
        return

    if original.public_credit_name == instance.public_credit_name:
        # public_credit_name has not been changed
        return

    if not instance.public_credit_name_approved:
        # instance.public_credit_name_approved is already False, no need to notify again
        return

    # put the message together
    message='User {username} changed public credit name. please review and act accordingly: https://bornhack.dk/admin/profiles/profile/{uuid}/change/'.format(
        username=instance.name,
        uuid=instance.uuid
    )

    # trigger the event
    handle_team_event(
        eventtype='public_credit_name_changed',
        irc_message=message,
    )

