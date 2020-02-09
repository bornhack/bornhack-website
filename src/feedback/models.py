from django.db import models

from utils.models import CampRelatedModel, UUIDModel


class Feedback(CampRelatedModel, UUIDModel):
    camp = models.ForeignKey("camps.Camp", on_delete=models.PROTECT)
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    feedback = models.TextField()
