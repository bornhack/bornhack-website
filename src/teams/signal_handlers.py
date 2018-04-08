from .email import add_new_membership_email
from ircbot.utils import add_irc_message
from django.conf import settings
import logging
logger = logging.getLogger("bornhack.%s" % __name__)


def teammember_saved(sender, instance, created, **kwargs):
    """
    This signal handler is called whenever a TeamMember instance is saved
    """
    # if this is a new unapproved teammember send a mail to team responsibles
    if created and not instance.approved:
        # call the mail sending function
        if not add_new_membership_email(instance):
            logger.error('Error adding email to outgoing queue')

    # if this team has a private and bot-managed IRC channel check if we need to add this member to ACL
    if instance.team.irc_channel and instance.team.irc_channel_managed and instance.team.irc_channel_private:
        # if this membership is approved and the member has entered a nickserv_username which not yet been added to the ACL
        if instance.approved and instance.user.profile.nickserv_username and not instance.irc_channel_acl_ok:
            add_team_channel_acl(instance)

def teammember_deleted(sender, instance, **kwargs):
    """
    This signal handler is called whenever a TeamMember instance is deleted
    """
    if instance.irc_channel_acl_ok and instance.team.irc_channel and instance.team.irc_channel_managed and instance.team.irc_channel_private:
        # TODO: we have an ACL entry that needs to be deleted but the bot does not handle it automatically
        add_irc_message(instance.team.irc_channel_name, "Teammember %s removed from team. Please remove NickServ user %s from IRC channel ACL manually!" % (instance.user.get_public_credit_name, instance.user.profile.nickserv_username))

