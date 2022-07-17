from django.db import models
from django_prometheus.models import ExportModelOperationsMixin

from utils.models import CampRelatedModel
from utils.models import UUIDModel


class Feedback(ExportModelOperationsMixin("feedback"), CampRelatedModel, UUIDModel):
    camp = models.ForeignKey("camps.Camp", on_delete=models.PROTECT)
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    feedback = models.TextField()
