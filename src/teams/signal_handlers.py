import logging
from typing import Any

logger = logging.getLogger(f"bornhack.{__name__}")


def teammember_saved(sender, instance, created, **kwargs: dict[str, Any]) -> None:
    """This signal handler is called whenever a TeamMember instance is saved"""
    # if this is a new unapproved teammember send a mail to team responsibles
    if created and not instance.approved:
        # call the mail sending function
        # late import to please django 3.2 or "django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet."
        from .email import add_new_membership_email

        if not add_new_membership_email(instance):
            logger.error("Error adding email to outgoing queue")


def teammember_deleted(sender, instance, **kwargs: dict[str, Any]) -> None:
    """This signal handler is called whenever a TeamMember instance is deleted"""
    if instance.team.private_irc_channel_name and instance.team.private_irc_channel_managed:
        # TODO: remove user from private channel ACL
        pass

    if instance.team.public_irc_channel_name and instance.team.public_irc_channel_managed:
        # TODO: remove user from public channel ACL
        pass
