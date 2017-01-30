from __future__ import unicode_literals
from utils.models import UUIDModel, CreatedUpdatedModel
from django.db import models


class OutgoingIrcMessage(CreatedUpdatedModel):
    target = models.CharField(max_length=100)
    message = models.CharField(max_length=200)
    processed = models.BooleanField(default=False)

