from .email import add_new_membership_email

def add_responsible_email(sender, instance, created, **kwargs):
    """
    This signal handler is called whenever a TeamMember instance is saved 
    """
    # only send mail is a new TeamMember was created
    if not created:
        return

    # only send mail if the membership is not approved
    if instance.approved:
        return

    # call the mail sending function
    if not add_new_membership_email(instance):
        logger.error('Error adding email to outgoing queue')

