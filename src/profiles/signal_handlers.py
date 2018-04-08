from django.db.models.signals import (
    post_save,
    pre_save
)
from events.handler import handle_team_event
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def create_profile(sender, created, instance, **kwargs):
    """
    Signal handler called after a User object is saved.
    Creates a Profile object when the User object was just created.
    """
    from .models import Profile
    if created:
        Profile.objects.create(user=instance)


def profile_pre_save(sender, instance, **kwargs):
    """
    Signal handler called before a Profile object is saved.
    """
    try:
        original = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        original = None
    logger.debug("inside profile_pre_save with instance.nickserv_username=%s and original.nickserv_username=%s" % (instance.nickserv_username, original.nickserv_username))

    public_credit_name_changed(instance, original)
    nickserv_username_changed(instance, original)


def public_credit_name_changed(instance, original):
    """
    Checks if a users public_credit_name has been changed, and triggers a public_credit_name_changed event if so
    """
    if original.public_credit_name == instance.public_credit_name:
        # public_credit_name has not been changed
        return

    if original.public_credit_name and not original.public_credit_name_approved:
        # the original.public_credit_name was not approved, no need to notify again
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


def nickserv_username_changed(instance, original):
    """
    Check if profile.nickserv_username was changed, and uncheck irc_channel_acl_ok if so
    This will be picked up by the IRC bot and fixed as needed
    """
    if instance.nickserv_username and instance.nickserv_username != original.nickserv_username:
        logger.debug("profile.nickserv_username changed for user %s, setting irc_channel_acl_ok=False" % instance.user.username)

        # find team memberships for this user
        from teams.models import TeamMember
        memberships = TeamMember.objects.filter(
            user=instance.user,
            approved=True,
            team__irc_channel=True,
            team__irc_channel_managed=True,
            team__irc_channel_private=True,
        )

        # loop over memberships
        for membership in memberships:
            membership.irc_channel_acl_ok = False
            membership.save()

