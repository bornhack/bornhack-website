import logging

from events.handler import handle_team_event

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

    public_credit_name_changed(instance, original)
    nickserv_username_changed(instance, original)


def public_credit_name_changed(instance, original):
    """
    Checks if a users public_credit_name has been changed, and triggers a public_credit_name_changed event if so
    """
    if original and original.public_credit_name == instance.public_credit_name:
        # public_credit_name has not been changed
        return

    if (
        original
        and original.public_credit_name
        and not original.public_credit_name_approved
    ):
        # the original.public_credit_name was not approved, no need to notify again
        return

    # put the message together
    message = "User {username} changed public credit name. please review and act accordingly: https://bornhack.dk/admin/profiles/profile/{uuid}/change/".format(
        username=instance.name,
        uuid=instance.uuid,
    )

    # trigger the event
    handle_team_event(eventtype="public_credit_name_changed", irc_message=message)


def nickserv_username_changed(instance, original):
    """
    Check if profile.nickserv_username was changed, and check irc_acl_fix_needed if so
    This will be picked up by the IRC bot and fixed as needed
    """
    if (
        instance.nickserv_username
        and original
        and instance.nickserv_username != original.nickserv_username
    ):
        logger.debug(
            "profile.nickserv_username changed for user %s, setting membership.irc_acl_fix_needed=True"
            % instance.user.username,
        )

        # find team memberships for this user
        from teams.models import TeamMember

        memberships = TeamMember.objects.filter(user=instance.user, approved=True)

        # loop over memberships
        for membership in memberships:
            if (
                not membership.team.public_irc_channel_name
                and not membership.team.private_irc_channel_name
            ):
                # no irc channels for this team
                continue
            if (
                not membership.team.public_irc_channel_managed
                and not membership.team.private_irc_channel_managed
            ):
                # irc channel(s) are not managed for this team
                continue

            # ok, mark this membership as in need of fixing
            membership.irc_acl_fix_needed = True
            membership.save()


def set_session_on_login(sender, request, user, **kwargs):
    """Signal handler called on_login to set session["theme"] from the user profile."""
    request.session["theme"] = request.user.profile.theme
