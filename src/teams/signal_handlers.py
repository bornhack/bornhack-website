import logging
from django.conf import settings


logger = logging.getLogger("bornhack.%s" % __name__)


def teammember_saved(sender, instance, created, **kwargs):
    """
    This signal handler is called whenever a TeamMember instance is saved
    """
    # if this is a new unapproved teammember send a mail to team leads
    if created and not instance.approved:
        # call the mail sending function
        # late import to please django 3.2 or "django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet."
        from .email import add_new_membership_email

        if not add_new_membership_email(instance):
            logger.error("Error adding email to outgoing queue")
        return

    # make sure the teams group membership and permission is uptodate
    instance.update_group_membership()
    instance.update_team_lead_permissions()


def teammember_deleted(sender, instance, **kwargs):
    """
    This signal handler is called whenever a TeamMember instance is deleted
    """
    if (
        instance.team.private_irc_channel_name
        and instance.team.private_irc_channel_managed
    ):
        # TODO: remove user from private channel ACL
        pass

    if (
        instance.team.public_irc_channel_name
        and instance.team.public_irc_channel_managed
    ):
        # TODO: remove user from public channel ACL
        pass

    # make sure the teams group membership is uptodate
    instance.update_group_membership(deleted=True)
    instance.update_team_lead_permissions(deleted=True)


def team_saved(sender, instance, created, **kwargs):
    """
    This signal handler is called whenever a Team instance is saved
    """
    # late imports
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from camps.models import Permission as CampPermission

    perm_content_type = ContentType.objects.get_for_model(CampPermission)
    # make sure required permissions exist in the database
    for name, desc in settings.BORNHACK_TEAM_PERMISSIONS.items():
        codename = f"{instance.slug}_team_{name}"
        perm, created = Permission.objects.get_or_create(
            codename=codename,
            content_type=perm_content_type,
            defaults={
                "name": f"{instance.name} {desc}",
            },
        )
        if created:
            logger.debug(f"Created new permission camps.{codename}")
