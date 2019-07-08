from .models import Team


def get_team_from_irc_channel(channel):
    """
    Returns a Team object given an IRC channel name, if possible
    """
    # check if this channel is a private_irc_channel for a team
    try:
        return Team.objects.get(private_irc_channel_name=channel)
    except Team.DoesNotExist:
        pass

    # check if this channel is a public_irc_channel for a team
    try:
        return Team.objects.get(public_irc_channel_name=channel)
    except Team.DoesNotExist:
        return False
