from django.db import models

from utils.models import UUIDModel, CreatedUpdatedModel


class Feedback(UUIDModel, CreatedUpdatedModel):
    user = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    feedback = models.TextField()
