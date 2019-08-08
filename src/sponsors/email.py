from utils.email import add_outgoing_email


def add_sponsorticket_email(sponsor):
    # put formatdict together
    formatdict = {
        "sponsor": sponsor,
    }

    subject = "BornHack %s Sponsor Tickets" % sponsor.camp.title
    attachments = []
    for ticket in sponsor.sponsorticket_set.all():
        path = "sponsor_ticket_%s" % ticket.uuid
        attachments.append()

    # add email to outgoing email queue
    return add_outgoing_email(
        text_template="emails/sponsorticket_email.txt",
        html_template="emails/sponsorticket_email.html",
        to_recipients=sponsor.ticket_email,
        formatdict=formatdict,
        subject=subject,
        attachments=attachments
    )

