from django.db import models

from utils.models import CampRelatedModel, UUIDModel


class Reimbursement(CampRelatedModel, UUIDModel):
    camp = models.ForeignKey('camps.Camp', on_delete=models.PROTECT)
    user = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    description = models.TextField()
    receipt = models.ImageField()
