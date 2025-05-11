from __future__ import annotations

import logging

from django.core.exceptions import ObjectDoesNotExist

from teams.models import Team
from utils.email import add_outgoing_email

logger = logging.getLogger("bornhack.%s" % __name__)


def add_village_approve_email(village):
    formatdict = {"village": village}

    try:
        orga_team = Team.objects.get(camp=village.camp, name="Orga")
    except ObjectDoesNotExist as e:
        logger.info(f"There is no team with name Orga: {e}")
        return False

    return add_outgoing_email(
        responsible_team=orga_team,
        text_template="emails/village_approve.txt",
        html_template="emails/village_approve.html",
        to_recipients="info@bornhack.dk",
        formatdict=formatdict,
        subject="Village created or updated, approval needed",
        hold=False,
    )
