from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CreatedUpdatedModel


class OutgoingIrcMessage(
    ExportModelOperationsMixin("outgoing_irc_message"),
    CreatedUpdatedModel,
):
    target = models.CharField(max_length=100)
    message = models.CharField(max_length=200)
    processed = models.BooleanField(default=False)
    timeout = models.DateTimeField()
    expired = models.BooleanField(default=False)

    def __str__(self):
        return "PRIVMSG {} {} ({})".format(
            self.target,
            self.message,
            "processed" if self.processed else "unprocessed",
        )

    def clean(self):
        if not self.pk:
            # this is a new outgoing message being saved
            if self.timeout < timezone.now():
                raise ValidationError({"timeout": "The timeout can not be in the past"})
